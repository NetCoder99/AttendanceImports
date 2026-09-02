# ---------------------------------------------------------------------------------------------------------------------
# sqlacodegen sqlite:///C:\Users\jdugger01\AppData\Roaming\Attendance\AttendanceV3.db --tables students
# ---------------------------------------------------------------------------------------------------------------------

import logging
import logging.config
import loggingConf

from imports.import_students import importStudents

logging_config_dict = loggingConf.LOGGING_CONFIG
logging.config.dictConfig(logging_config_dict)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        logging.basicConfig(filename='AttendanceImports.log', level=logging.INFO)
        logger.info('-----------------------------------------------------------------')
        logger.info('AttendanceImports - Started')
        importStudents("AttendanceV2_20260612.db", "AttendanceV3.db")
        logger.info('AttendanceImports - Started')
    except Exception as ex:
        logger.error(f'AttendanceImports - Failed : {str(ex)}')
