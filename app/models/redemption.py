from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.config.database import Base
from app.utils.datetime_utils import get_ist_now


class Redemption(Base):
    __tablename__ = "redemptions"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("users.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    points_used = Column(Integer)
    amount_discounted = Column(Integer)  # e.g. 100 points = 10 INR (stored as int)

    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_ist_now)
    updated_at = Column(DateTime, default=get_ist_now, onupdate=get_ist_now)
