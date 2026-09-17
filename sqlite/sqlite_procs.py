import os
import platform
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_session = None
#db_name    = 'AttendanceV3.db'

def getDbPath(db_name: str = 'AttendanceV3.db'):
    if platform.system() == 'Windows':
        return os.path.join(os.getenv('APPDATA'), 'Attendance', db_name)
    else:

        # /home/johnd/.local/share
        db_path_str = os.path.join(os.getenv('HOME'), '.local', 'share', db_name)
        file_path = Path(db_path_str)
        if file_path.is_file():
            return file_path
        return os.path.join('/', 'Attendance', db_name)

def getDbSession(db_path: str = getDbPath()):
    global db_session
    if db_session is None:
        engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=engine)
        db_session = Session()
    return db_session





