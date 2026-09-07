import io
import logging
from datetime import datetime

from dateutil.parser import parse
from sqlalchemy import select, inspect

import constants
from imports.check_ranks import GetCrntStudentRank, GetBasedOnAttendanceTotalCountSrce
from imports.import_common import getImportSession, cloneRecord
from models.data_models import Students
from models.output_models import StudentImageDetails
from models.srce_models import SrceStudents
from sqlite.sqlite_alchemy import getAlchemySession
from sqlite.sqlite_procs import getDbPath
from PIL import Image

logger = logging.getLogger(__name__)

db_session_srce = None
db_session_dest = None


def importStudents(srce_db_name: str, dest_db_name: str):
    global db_session_srce
    global db_session_dest
    excep_list    = []
    import_counts = {'records_read' : 0, 'records_inserted' : 0, 'records_updated' : 0, 'records_error' : 0 }
    try:
        srce_db = getDbPath(srce_db_name)
        dest_db = getDbPath(dest_db_name)

        db_session_srce = getImportSession(srce_db)
        db_session_dest = getAlchemySession(dest_db)

        logger.info(f'srce_db: {srce_db}')

        for student_record_srce in db_session_srce.query(SrceStudents):
            student_record_dest = GetCrntStudentRecord(db_session_dest, student_record_srce.badgeNumber)
            if not student_record_dest:
                new_student_record = GetNewStudentRecord(student_record_srce)
                logger.info(f'inserting student: {student_record_srce.badgeNumber}')
                db_session_dest.add(new_student_record)
                db_session_dest.commit()
                import_counts['records_inserted'] = import_counts['records_inserted'] + 1

            # else:
            #     ValidateStudentFields(student_record_srce, student_record_dest)
            #     inspected = inspect(student_record_dest)
            #     if db_session_dest.is_modified(student_record_dest):
            #         logger.info(f'updating student: {student_record_srce.badgeNumber}')
            #         DisplayOldAndNewValues(student_record_dest)
            #     else:
            #         logger.info(f'no updates for  : {student_record_srce.badgeNumber}')

            # student_record_dest = cloneRecord(student_record)
            # student_record_dest.createDateTime = student_record_dest.createDateTime if student_record_dest.createDateTime else updateDateTime
            # student_record_dest.updateDateTime = updateDateTime
            # db_session_dest.merge(student_record_dest)
            # #db_session_dest.commit()

    except Exception as ex:
        logger.error(str(ex))
        excep_list.append(ex)

    if len(excep_list) > 0:
        raise excep_list[0]
    else:
        return import_counts


def GetNewStudentRecord(student_record_srce: SrceStudents) -> Students:
    global db_session_srce
    global db_session_dest
    try:
        image_details = GetImageDetails(student_record_srce.badgeNumber, student_record_srce.studentImage)
        rtn_student_record = Students()
        rtn_student_record.badgeNumber = student_record_srce.badgeNumber
        rtn_student_record.firstName   = student_record_srce.firstName
        rtn_student_record.lastName    = student_record_srce.lastName
        rtn_student_record.namePrefix  = student_record_srce.namePrefix
        rtn_student_record.email       = student_record_srce.email
        rtn_student_record.address     = student_record_srce.address
        rtn_student_record.address2    = student_record_srce.address2
        rtn_student_record.city        = student_record_srce.city
        rtn_student_record.country     = student_record_srce.country
        rtn_student_record.state       = student_record_srce.state
        rtn_student_record.zip         = student_record_srce.zip
        rtn_student_record.birthDate   = student_record_srce.birthDate
        rtn_student_record.phoneHome   = student_record_srce.phoneHome
        rtn_student_record.phoneMobile = student_record_srce.phoneMobile
        rtn_student_record.status      = student_record_srce.status
        rtn_student_record.memberSince        = student_record_srce.memberSince
        rtn_student_record.gender             = student_record_srce.gender
        rtn_student_record.ethnicity          = student_record_srce.ethnicity
        rtn_student_record.studentImageBytes  = student_record_srce.studentImage
        rtn_student_record.studentImagePath   = student_record_srce.studentImagePath
        rtn_student_record.studentImageBase64 = student_record_srce.imageBase64
        rtn_student_record.middleName         = student_record_srce.middleName
        rtn_student_record.studentImageName   = f'{student_record_srce.firstName}_{student_record_srce.lastName}.{image_details.image_type.lower()}'
        rtn_student_record.studentImageType   = image_details.image_type

        student_rank  = GetBasedOnAttendanceTotalCountSrce(db_session_srce, rtn_student_record)
        rtn_student_record.currentRankNum       = student_rank.currentRankNum
        rtn_student_record.currentRankName      = student_rank.currentRankName
        rtn_student_record.currentStripeId      = student_rank.currentStripeId
        rtn_student_record.currentStripeName    = student_rank.currentStripeName
        rtn_student_record.studentPromotionDate = datetime.now().strftime(constants.fmtDateTime)

        rtn_student_record.createDateTime  = student_record_srce.memberSince
        member_since_datetime = parse(student_record_srce.memberSince, fuzzy=False).strftime(constants.fmtDateTime)
        rtn_student_record.memberSinceDate = member_since_datetime
        return rtn_student_record
    except Exception as ex:
        print(f'Error: {str(ex)}')
        raise ex


# -----------------------------------------------------------------------------------
# update missing fields on the source student record
# -----------------------------------------------------------------------------------
def ValidateStudentFields(student_record_srce: SrceStudents, student_record_dest: Students):
    if not student_record_dest.studentImageBase64 and student_record_srce.imageBase64:
        logger.info(f'updating student image: {student_record_srce.badgeNumber}')

    if not student_record_dest.createDateTime:
        if student_record_srce.memberSince:
            logger.info(f'updating create date: {student_record_srce.badgeNumber} : {student_record_srce.memberSince}')
            student_record_dest.createDateTime = student_record_srce.memberSince
        else:
            logger.info(f'updating create date (default): {student_record_srce.badgeNumber} : {datetime.now().strftime(constants.fmtDateTime)}')
            student_record_dest.createDateTime = datetime.now().strftime(constants.fmtDateTime)





# -----------------------------------------------------------------------------------
def DisplayOldAndNewValues(student_record_dest: Students):
    mapper = inspect(student_record_dest)
    for column in mapper.attrs:
        print(f"Column name: {column.key}, Is Modified: {column.state.modified}")

# -----------------------------------------------------------------------------------
# commonly used function to get the student record
# -----------------------------------------------------------------------------------
def GetCrntStudentRecord(db_session, badge_number: int) -> Students:
    student_list_stmt = select(Students).where(Students.badgeNumber == badge_number)
    return db_session.scalars(student_list_stmt).first()

def GetImageDetails(badge_number: int, studentImageBytes: bytes) -> StudentImageDetails:
    try:
        student_image_details = StudentImageDetails.construct()
        student_image_details.badge_number = badge_number
        with Image.open(io.BytesIO(studentImageBytes)) as img:
            exif = img.getexif()
            student_image_details.image_type = img.format
            return student_image_details
            # orientation = exif.get(0x0112, 1)
            # if orientation == 3:
            #     img = img.rotate(180, expand=True)
            # elif orientation == 6:
            #     img = img.rotate(270, expand=True)
            # elif orientation == 8:
            #     img = img.rotate(90, expand=True)
            #
            # if img.mode in ("RGBA", "P"):
            #     background = Image.new("RGB", img.size, (255, 255, 255))
            #     background.paste(img, mask=img.split()[3])
            #     max_size = (300, 300)
            #     background.thumbnail(max_size, Image.Resampling.LANCZOS)
            #     background.save(newFilePath)
            #     background.close()
            # else:
            #     max_size = (300, 300)
            #     img.thumbnail(max_size, Image.Resampling.LANCZOS)
            #     img.save(newFilePath)
            #     img.close()
            return newFilePath
    except Exception as ex:
        print(f"Error processing image: {ex}")
        raise ex
