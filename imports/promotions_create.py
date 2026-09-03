# ---------------------------------------------------------------------------------------
from sqlalchemy import select

import constants
from models.data_models import Students, Promotions, Requirements
from datetime import datetime

from models.output_models import NewPromotionRecord
from sqlite.sqlite_alchemy import getAlchemySession

db_session = getAlchemySession()

def InsNewPromotionRecord(student_record: Students,  promotion_params: NewPromotionRecord) -> Promotions:
    try:
        ValidatePromotionParams(promotion_params)
        new_promotion_record = Promotions()
        new_promotion_record.studentName      = f'{student_record.firstName} {student_record.lastName}'
        new_promotion_record.studentFirstName = student_record.firstName
        new_promotion_record.studentLastName  = student_record.lastName
        new_promotion_record.badgeNumber      = student_record.badgeNumber
        new_promotion_record.beltId      = promotion_params.belt_id
        new_promotion_record.beltTitle   = promotion_params.belt_name
        new_promotion_record.stripeId    = promotion_params.stripe_id
        new_promotion_record.stripeTitle = promotion_params.stripe_name
        if promotion_params.belt_id != student_record.currentRankNum:
            new_promotion_record.promotionType = 'Belt'
        else:
            new_promotion_record.promotionType = 'Stripe'
        if promotion_params.comments == '':
            new_promotion_record.comments = "Promotion from api"
        else:
            new_promotion_record.comments = promotion_params.comments
        new_promotion_record.promotionDate  = promotion_params.promotion_date.strftime(constants.fmtDateTime)
        new_promotion_record.createDateTime = datetime.now().strftime(constants.fmtDateTime)
        new_promotion_record.createDateTime = datetime.now().strftime(constants.fmtDateTime)
        db_session.add(new_promotion_record)
        if promotion_params.post_flag:
            db_session.commit()
        return new_promotion_record
    except Exception as ex:
        print(f'Error: {str(ex)}')
        raise ex

def ValidatePromotionParams(promotion_params: NewPromotionRecord):
    belt_record = db_session.scalars(
        select(Requirements).where(Requirements.beltId == promotion_params.belt_id)
    ).first()
    if not belt_record:
        raise Exception(f"Belt Id was not found: {promotion_params.belt_id}.")
    promotion_params.belt_name = belt_record.beltTitle

    stripe_record = db_session.scalars(
        select(Requirements).where(Requirements.stripeId == promotion_params.stripe_id)
    ).first()
    if not stripe_record:
        raise Exception(f"Stripe Id was not found: {promotion_params.stripe_id}.")
    promotion_params.stripe_name = stripe_record.stripeTitle

    requirement_record = db_session.scalars(
        select(Requirements)
        .where(Requirements.beltId == promotion_params.belt_id)
        .where(Requirements.stripeId == promotion_params.stripe_id)
    ).all()
    if not requirement_record:
        raise Exception(f"Stripe Id was not valid for that belt id: {promotion_params.belt_id}:{promotion_params.stripe_id}.")

    duplicate_record = db_session.scalars(
        select(Promotions)
        .where(Promotions.badgeNumber == promotion_params.badge_number)
        .where(Promotions.beltId      == promotion_params.belt_id)
        .where(Promotions.stripeId    == promotion_params.stripe_id)
    ).first()
    if duplicate_record:
        raise Exception(f"Duplicated promotion record not inserted: {duplicate_record.promotionId} .")

    return True