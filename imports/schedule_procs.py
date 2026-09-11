import logging
from datetime import datetime, time, date, timedelta

import constants
from models.data_models import Classes
from sqlite.sqlite_procs import getDbSession

logger = logging.getLogger(__name__)

db_session = getDbSession()

# --------------------------------------------------------------------
# Search for a class within the start and stop times
# --------------------------------------------------------------------
def GetCurrentClass(checkin_datetime: date = datetime.now(), before_interval: int = 15, after_interval: int = 15):

    day_of_week: int = checkin_datetime.weekday() + 1
    #class_times = Classes.objects.filter(class_day_of_week=today).order_by('class_start_time')
    class_times = db_session.query(Classes).filter_by(classDayOfWeek=day_of_week)

    #current_date = datetime.now()
    current_date_str = checkin_datetime.strftime("%m/%d/%Y")
    date_format = "%m/%d/%Y %I:%M %p"
    for class_record in class_times:
        start_checkin_str  = current_date_str + ' ' + class_record.classStartTime
        start_checkin_date = datetime.strptime(start_checkin_str, date_format)
        finis_checkin_str  = current_date_str + ' ' + class_record.classFinisTime
        finis_checkin_date = datetime.strptime(finis_checkin_str, date_format)

        start_checkin_time = start_checkin_date - timedelta(minutes=before_interval)
        finis_checkin_time = start_checkin_date + timedelta(minutes=after_interval)

        DisplayClassDateTimes(start_checkin_time, finis_checkin_time, checkin_datetime)

        if start_checkin_time <= checkin_datetime <= finis_checkin_time:
            return class_record

        # if start_checkin_date <= checkin_datetime <= finis_checkin_date:
        #     return class_record

    return None

def DisplayClassDateTimes(start_datetime: date, finis_datetime: date, checkin_date: date = None):
    if checkin_date:
        logger.info(
            f'{checkin_date.strftime(constants.dayNameAbbr)} - '
            f'{start_datetime.strftime(constants.fmtDateTime3)} '
            f'{finis_datetime.strftime(constants.fmtDateTime3)} '
            f'{checkin_date.strftime(constants.fmtDateTime3)}'
        )
    else:
        logger.info(
            f'{checkin_date.strftime(constants.dayNameAbbr)} - '
            f'{start_datetime.strftime(constants.fmtDateTime3)} '
            f'{finis_datetime.strftime(constants.fmtDateTime3)} '
        )
