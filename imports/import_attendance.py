import logging
import traceback
from datetime import datetime

from dateutil.parser import parse
from sqlalchemy import select, inspect

import constants
from imports.import_common import getImportSession, cloneRecord
from imports.schedule_procs import GetCurrentClass
from models.data_models import Students, Attendance
from models.srce_models import SrceStudents, SrceAttendance
from sqlite.sqlite_alchemy import getAlchemySession
from sqlite.sqlite_procs import getDbPath

logger = logging.getLogger(__name__)

def importAttendanceRecords(srce_db_name: str, dest_db_name: str):
    excep_list    = []
    import_counts = {'import_table': 'Students', 'records_read' : 0, 'records_inserted' : 0, 'records_updated' : 0, 'records_error' : 0 }
    attendance_count_srce = 0
    try:
        db_session_srce = getAlchemySession(srce_db_name)
        db_session_dest = getAlchemySession(dest_db_name)

        # attendance_list_stmt = (select(SrceAttendance)
        #                         .where(SrceAttendance.badgeNumber == '10083')
        #                         .order_by(SrceAttendance.attendance_id)
        #                         )
        attendance_list_stmt = select(SrceAttendance).order_by(SrceAttendance.badgeNumber)
        # attendance_list_stmt = select(SrceAttendance).group_by(SrceAttendance.badgeNumber, SrceAttendance.checkinDateTime).order_by(SrceAttendance.badgeNumber)

        attendance_list = db_session_srce.scalars(attendance_list_stmt).all()
        for attendance_record_srce in attendance_list:
            attendance_count_srce += 1
            # logger.info(attendance_record_srce.attendance_id)
            attendance_records_dest = GetCrntAttendanceRecord(
                db_session_dest,
                attendance_record_srce.badgeNumber,
                attendance_record_srce.checkinDateTime
            )
            if len(attendance_records_dest) == 0:
                import_counts['records_inserted'] = import_counts['records_inserted'] + 1
                new_attendance_record = GetNewAttendanceRecord(
                    db_session_dest,
                    attendance_record_srce
                )
                db_session_dest.add(new_attendance_record)
                db_session_dest.commit()
                logger.info(f'insert   : '
                            f'{attendance_record_srce.attendance_id} : '
                            f'{attendance_record_srce.badgeNumber} : '
                            f'{attendance_record_srce.checkinDateTime}')
            elif len(attendance_records_dest) == 1:
                import_counts['records_updated'] = import_counts['records_updated'] + 1
                test = False
                # logger.info(f'updating : '
                #             f'{attendance_records_dest[0].attendance_id} : '
                #             f'{attendance_records_dest[0].badgeNumber} : '
                #             f'{attendance_records_dest[0].checkinDateTime}')
            elif len(attendance_records_dest) == 2:
                are_duplicates = compare_record_columns(attendance_records_dest[0], attendance_records_dest[1], {'attendance_id'})
                logger.info(f'duplicate dest: {are_duplicates} '
                            f'{attendance_records_dest[0].attendance_id} : '
                            f'{attendance_records_dest[0].badgeNumber} : '
                            f'{attendance_records_dest[0].checkinDateTime}'
                            f' == '
                            f'{attendance_records_dest[1].attendance_id} : '
                            f'{attendance_records_dest[1].badgeNumber} : '
                            f'{attendance_records_dest[1].checkinDateTime}'
                            )
                #if are_duplicates:
                test = False
            else:
                logger.info(f'invalid  : '
                            f'{attendance_records_dest[0].attendance_id} : '
                            f'{attendance_records_dest[0].badgeNumber} : '
                            f'{attendance_records_dest[0].checkinDateTime}')

        logger.info(f'{attendance_count_srce} source records processed')

    except Exception as ex:
        logger.error(str(ex))
        excep_list.append(ex)

    if len(excep_list) > 0:
        raise excep_list[0]
    else:
        return import_counts


def compare_record_columns(obj1, obj2, ignore_keys=None):
    if ignore_keys is None:
        ignore_keys = {'id', 'created_at', 'updated_at'}
    mapper = inspect(obj1.__class__)
    for column in mapper.attrs:
        key = column.key
        if key in ignore_keys:
            continue
        if getattr(obj1, key) != getattr(obj2, key):
            return False
    return True


def records_have_same_values(obj1, obj2):
    # Copy dictionaries to avoid modifying the original objects
    dict1 = obj1.__dict__.copy()
    dict2 = obj2.__dict__.copy()

    # Remove SQLAlchemy internal tracking state
    dict1.pop('_sa_instance_state', None)
    dict2.pop('_sa_instance_state', None)

    return dict1 == dict2

# -----------------------------------------------------------------------------------
# commonly used function to get the student record
# -----------------------------------------------------------------------------------
def GetCrntAttendanceRecord(db_session, badge_number: int, checkin_datetime: str) -> list[Attendance]:
    if checkin_datetime.endswith('00'):
        temp_attendance_date = parse(checkin_datetime, fuzzy=False).strftime(constants.fmtDateTime2)
    else:
        temp_attendance_date = parse(checkin_datetime, fuzzy=False).strftime(constants.fmtDateTime)

    # if badge_number == 1006:
    #     logger.info(f'search params: {badge_number} : {checkin_datetime}')
    attendance_stmt = (select(Attendance)
                         .where(Attendance.badgeNumber     == badge_number)
                         .where(Attendance.checkinDateTime == temp_attendance_date)
                      )
    rtn_list = db_session.scalars(attendance_stmt).all()
    # if len(rtn_list) != 1:
    #     logger.info(f'search params: {badge_number} : {checkin_datetime}')

    return rtn_list  #db_session.scalars(attendance_stmt).all()

# -----------------------------------------------------------------------------------
# commonly used function to get the student record
# -----------------------------------------------------------------------------------
def GetNewAttendanceRecord(db_session, attendance_record_srce: SrceAttendance) -> Attendance:
    try:
        new_attendance_record = Attendance()
        new_attendance_record.badgeNumber = attendance_record_srce.badgeNumber
        # new_attendance_record.attendance_id     =
        # new_attendance_record.badgeNumber       =

        temp_checkin_datetime = parse(attendance_record_srce.checkinDateTime, fuzzy=False)
        new_attendance_record.checkinDateTime   = temp_checkin_datetime.strftime(constants.fmtDateTime)
        new_attendance_record.checkinDate       = temp_checkin_datetime.strftime(constants.fmtDate)
        new_attendance_record.checkinTime       = temp_checkin_datetime.strftime(constants.fmtTime)

        student_name_parts = attendance_record_srce.studentName.split()

        new_attendance_record.studentFirstName  = student_name_parts[0]
        new_attendance_record.studentLastName   = student_name_parts[1] if len(student_name_parts) else ''
        new_attendance_record.studentStatus     = attendance_record_srce.studentStatus
        # new_attendance_record.studentRankNum    = attendance_record_srce.rankName
        new_attendance_record.studentRankName   = attendance_record_srce.rankName
        # new_attendance_record.studentStripeId   =
        # new_attendance_record.studentStripeName =
        # new_attendance_record.classNum          =

        #temp_start_time = attendance_record_srce.studentName.split('@')
        selected_class = GetCurrentClass(temp_checkin_datetime)
        if selected_class:
            new_attendance_record.classNum          = selected_class.classNum
            new_attendance_record.className         = selected_class.className
            new_attendance_record.classStartTime    = selected_class.classStartTime
            new_attendance_record.styleNum          = selected_class.styleNum
            new_attendance_record.styleName         = selected_class.styleName
        else:
            logger.info(f'No class found: {temp_checkin_datetime.strftime(constants.fmtDateTime)}')
        # new_attendance_record.appliesPromotion  =
        return new_attendance_record
    except Exception as ex:
        traceback.print_exc()
        logger.error(str(ex))
        raise ex
