import datetime

from pydantic import BaseModel

class AttendanceCounts(BaseModel):
    attendance_count_total: int
    attendance_count_since_belt: int
    attendance_count_since_stripe: int

class StudentRankFields(BaseModel):
    currentRankNum : int
    currentRankName : str
    currentStripeId : int
    currentStripeName : str
    studentPromotionDate : datetime.datetime
    attendanceCount : AttendanceCounts | None = None
    rankMessage : str

class NewPromotionRecord(BaseModel):
    badge_number: int
    belt_id : int
    belt_name : str
    stripe_id : int
    stripe_name : str
    promotion_date: datetime.datetime
    comments : str = ''
    post_flag: bool = False

class StudentImageDetails(BaseModel):
    badge_number: int
    image_type  : str



