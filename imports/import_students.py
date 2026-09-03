import logging
from datetime import datetime

from sqlalchemy import select, inspect

import constants
from imports.import_common import getImportSession, cloneRecord
from models.data_models import Students
from models.srce_models import SrceStudents
from sqlite.sqlite_alchemy import getAlchemySession
from sqlite.sqlite_procs import getDbPath

logger = logging.getLogger(__name__)

def importStudents(srce_db_name: str, dest_db_name: str):
    excep_list    = []
    import_counts = {'records_read' : 0, 'records_inserted' : 0, 'records_updated' : 0, 'records_error' : 0 }
    try:
        srce_db = getDbPath(srce_db_name)
        dest_db = getDbPath(dest_db_name)

        db_session_srce = getImportSession(srce_db)
        db_session_dest = getAlchemySession(dest_db)

        logger.info(f'srce_db: {srce_db}')

        for student_record_srce in db_session_srce.query(SrceStudents):
            #logger.info(f'badge number: {student_record.badgeNumber}')
            student_record_dest = GetCrntStudentRecord(db_session_dest, student_record_srce.badgeNumber)
            if not student_record_dest:
                logger.info(f'inserting student: {student_record_srce.badgeNumber}')
            else:
                ValidateStudentFields(student_record_srce, student_record_dest)
                inspected = inspect(student_record_dest)
                if db_session_dest.is_modified(student_record_dest):
                    logger.info(f'updating student: {student_record_srce.badgeNumber}')
                    DisplayOldAndNewValues(student_record_dest)
                else:
                    logger.info(f'no updates for  : {student_record_srce.badgeNumber}')

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