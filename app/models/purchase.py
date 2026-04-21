from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from app.config.database import Base
from app.utils.datetime_utils import get_ist_now


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("users.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    amount = Column(Integer)  # Gross amount before discount
    points_earned = Column(Integer)
    coupon_code = Column(String(50), nullable=True) # Kept for quick search
    coupon_usage_id = Column(Integer, ForeignKey("coupon_usages.id"), nullable=True)
    redemption_id = Column(Integer, ForeignKey("redemptions.id"), nullable=True)
    points_redeemed = Column(Integer, default=0)
    coupon_discount = Column(Integer, default=0)
    points_discount = Column(Integer, default=0)
    payable_amount = Column(Integer)  # Net amount after all discounts

    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_ist_now)
    updated_at = Column(DateTime, default=get_ist_now, onupdate=get_ist_now)
