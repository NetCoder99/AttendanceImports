import json
import logging
from datetime import datetime

from dateutil.parser import parse
from sqlalchemy import select, inspect, func

import constants
from imports.attendance_procs import GetAllAttendanceCounts
from imports.import_common import getImportSession, cloneRecord
from imports.promotions_create import InsNewPromotionRecord
from models.data_models import Students, Attendance, Promotions, Requirements
from models.output_models import StudentRankFields, NewPromotionRecord
from models.srce_models import SrceStudents, SrceAttendance
from sqlite.sqlite_alchemy import getAlchemySession
from sqlite.sqlite_procs import getDbPath

logger = logging.getLogger(__name__)

db_session = getAlchemySession()

def checkStudentRanks():
    excep_list = []
    import_counts = {'records_read': 0, 'records_inserted': 0, 'records_updated': 0, 'records_error': 0}
    try:
        students_list_stmt = (select(Students)
                              .where((Students.currentRankNum == None) | (Students.currentStripeId == None))
                              .order_by(Students.badgeNumber)
                              )
        students_list = db_session.scalars(students_list_stmt).all()
        for student_record in students_list:
            student_rank = GetCrntStudentRank(student_record)
            import_counts['records_updated'] = import_counts['records_updated'] + 1

            promotion_datetime = datetime.now()
            student_record.currentRankNum  = student_rank.currentRankNum
            student_record.currentRankName = student_rank.currentRankName
            student_record.currentStripeId = student_rank.currentStripeId
            student_record.currentStripeName = student_rank.currentStripeName
            student_record.studentPromotionDate = promotion_datetime.strftime(constants.fmtDateTime)

            promotion_params = NewPromotionRecord.construct()
            promotion_params.badge_number   = student_record.badgeNumber
            promotion_params.belt_id        = student_record.currentRankNum
            promotion_params.belt_name      = student_record.currentRankName
            promotion_params.stripe_id      = student_record.currentStripeId
            promotion_params.stripe_name    = student_record.currentStripeName
            promotion_params.promotion_date = promotion_datetime
            promotion_params.comments       = student_rank.rankMessage
            promotion_params.post_flag      = False
            InsNewPromotionRecord(student_record, promotion_params)

            logger.info(f'{student_record.badgeNumber} : {student_record.currentRankNum} : {student_rank.model_dump_json()}')

            db_session.commit()


    except Exception as ex:
        logger.error(str(ex))
        excep_list.append(ex)

    if len(excep_list) > 0:
        raise excep_list[0]
    else:
        return import_counts

# -----------------------------------------------------------------------------------
# during development the student rank/stripe is not reliably set, thus a complex
# set of calculations to determine the next available belt and/or stripe
# -----------------------------------------------------------------------------------
def GetCrntStudentRank(student_record: Students) -> StudentRankFields:
    try:
        # if rank and stripe are set on the student record then return that
        if student_record.currentRankNum and student_record.currentStripeId:
            student_rank = StudentRankFields.construct()
            student_rank.currentRankNum     = student_record.currentRankNum
            student_rank.currentRankName    = student_record.currentRankName
            student_rank.currentStripeId    = student_record.currentStripeId
            student_rank.currentStripeName  = student_record.currentStripeName
            student_rank.studentPromotionDate = student_record.studentPromotionDate
            student_rank.rankMessage = "From student record"
            return student_rank

        # if both rank and stripe are 'None' then check for a promotion record, use that if found
        last_promotion_record = GetLastPromotionRecord(student_record.badgeNumber)
        if last_promotion_record:
            #print(f'last_promotion_record : {last_promotion_record}')
            next_student_rank = GetNextFromLastPromotion(last_promotion_record)
            return next_student_rank

        # not set on student record and no promotion history, use total classes attended
        next_student_rank = GetBasedOnAttendanceTotalCount(student_record)
        return next_student_rank

    except Exception as ex:
        print(f'Error: {str(ex)}')
        raise ex

def GetNextFromLastPromotion(last_promotion_record: Promotions) -> StudentRankFields:
    try:
        next_student_rank = StudentRankFields.construct()
        crnt_requirement_stmt = (select(Requirements)
                                 .where(Requirements.beltId == last_promotion_record.beltId)
                                 .where(Requirements.stripeId == last_promotion_record.stripeId)
                                 .order_by(Requirements.promotionSeqNum))
        crnt_requirement_id = db_session.scalars(crnt_requirement_stmt).first().requirementId

        next_requirement_stmt = ((select(Requirements)
                                  .where(Requirements.requirementId > crnt_requirement_id))
                                 .order_by(Requirements.promotionSeqNum))
        next_requirement_record = db_session.scalars(next_requirement_stmt).first()

        next_student_rank.currentRankNum = next_requirement_record.beltId
        next_student_rank.currentRankName = next_requirement_record.beltTitle
        next_student_rank.currentStripeId = next_requirement_record.stripeId
        next_student_rank.currentStripeName = next_requirement_record.stripeTitle
        next_student_rank.studentPromotionDate = next_requirement_record.promotionDate
        next_student_rank.rankMessage = "From last promotion"
        return next_student_rank
    except Exception as ex:
        print(f'Error: {str(ex)}')
        raise ex


def GetBasedOnAttendanceTotalCount(student_record: Students) -> StudentRankFields:
    try:
        attendance_counts = GetAllAttendanceCounts(student_record.badgeNumber)
        student_rank = StudentRankFields.construct()
        student_rank.attendanceCount = attendance_counts
        requirement_record = (
            db_session.scalars(select(Requirements)
                               .where(Requirements.requiredClasses <= attendance_counts.attendance_count_total)
                               .order_by(Requirements.beltId.desc(), Requirements.promotionSeqNum.desc()))
            .first()
        )
        student_rank.currentRankNum = requirement_record.beltId
        student_rank.currentRankName = requirement_record.beltTitle
        student_rank.currentStripeId = requirement_record.stripeId
        student_rank.currentStripeName = requirement_record.stripeTitle
        student_rank.rankMessage = "From total attendance"
        return student_rank
    except Exception as ex:
        print(f'Error: {str(ex)}')
        raise ex
# ---------------------------------------------------------------------------------------
def GetAttendanceTotal(badge_number: int) -> int:
    attendance_total_stmt = (select(func.count())
                             .select_from(Attendance)
                             .where(Attendance.badgeNumber == badge_number))
    return db_session.scalar(attendance_total_stmt)

# ---------------------------------------------------------------------------------------
def GetPromotionRecords(badge_number: int) -> list[Promotions]:
    promotion_query_stmt = (select(Promotions)
                            .where(Promotions.badgeNumber == badge_number)
                            .order_by(Promotions.promotionDate.desc())
                            )
    return db_session.scalars(promotion_query_stmt).all()

def GetLastPromotionRecord(badge_number) -> Promotions:
    promotion_record_stmt = (select(Promotions)
                             .where(Promotions.badgeNumber == badge_number)
                             .order_by(Promotions.promotionDate.desc()))
    return db_session.scalars(promotion_record_stmt).first()

