from typing import Optional
import datetime

from sqlalchemy import ForeignKey, Index, Integer, LargeBinary, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class SrceStudents(Base):
    __tablename__ = 'students'

    badgeNumber: Mapped[int] = mapped_column(Integer, primary_key=True)
    firstName: Mapped[Optional[str]] = mapped_column(Text)
    lastName: Mapped[Optional[str]] = mapped_column(Text)
    namePrefix: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    address2: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(Text)
    country: Mapped[Optional[str]] = mapped_column(Text)
    state: Mapped[Optional[str]] = mapped_column(Text)
    zip: Mapped[Optional[str]] = mapped_column(Text)
    birthDate: Mapped[Optional[str]] = mapped_column(Text)
    phoneHome: Mapped[Optional[str]] = mapped_column(Text)
    phoneMobile: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(Text)
    memberSince: Mapped[Optional[str]] = mapped_column(Text)
    gender: Mapped[Optional[str]] = mapped_column(Text)
    currentRank: Mapped[Optional[str]] = mapped_column(Text)
    ethnicity: Mapped[Optional[str]] = mapped_column(Text)
    studentImage: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    studentImagePath: Mapped[Optional[str]] = mapped_column(Text)
    imageBase64: Mapped[Optional[str]] = mapped_column(Text)
    middleName: Mapped[Optional[str]] = mapped_column(Text)

class SrceAttendance(Base):
    __tablename__ = 'attendance'

    attendance_id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)
    badgeNumber: Mapped[Optional[int]] = mapped_column(Integer)
    checkinDateTime: Mapped[Optional[str]] = mapped_column(Text)
    checkinDate: Mapped[Optional[str]] = mapped_column(Text)
    checkinTime: Mapped[Optional[str]] = mapped_column(Text)
    studentName: Mapped[Optional[str]] = mapped_column(Text)
    studentStatus: Mapped[Optional[str]] = mapped_column(Text)
    className: Mapped[Optional[str]] = mapped_column(Text)
    rankName: Mapped[Optional[str]] = mapped_column(Text)
    classStartTime: Mapped[Optional[str]] = mapped_column(Text)
