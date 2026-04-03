from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.config.database import Base
from app.utils.datetime_utils import get_ist_now


class PointsLedger(Base):
    __tablename__ = "points_ledger"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("users.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    type = Column(String(10))  # "earn" or "redeem"
    points = Column(Integer)  # positive for earn, negative for redeem
    reference_id = Column(Integer, nullable=True)  # purchase_id or redemption_id

    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_ist_now)
    updated_at = Column(DateTime, default=get_ist_now, onupdate=get_ist_now)
