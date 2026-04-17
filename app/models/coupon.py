from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.utils.datetime_utils import get_ist_now
import enum

class CouponType(str, enum.Enum):
    percentage = "percentage"
    fixed = "fixed"

class EligibilityType(str, enum.Enum):
    all = "all"
    vip = "vip"
    new = "new"
    inactive = "inactive"

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("users.id")) # Multi-tenant isolation key
    
    code = Column(String(50), unique=True, index=True, nullable=False) # The unique alphanumeric code used by customers
    type = Column(Enum(CouponType), default=CouponType.percentage) # 'percentage' (e.g. 10%) or 'fixed' (e.g. ₹50)
    value = Column(Float, nullable=False) # The actual percentage or amount magnitude
    
    # Enterprise Grade Constraints
    max_discount_cap = Column(Float, nullable=True) # Financial Safety: Max ₹ saving allowed in 1 txn (Critical for % coupons)
    min_order_value = Column(Float, default=0.0) # Minimum bill amount required to authorize the coupon
    
    start_date = Column(DateTime, nullable=True) # Protocol activation timestamp
    expiry_date = Column(DateTime, nullable=True) # Protocol expiration timestamp (automatic expiry)
    
    max_usage_global = Column(Integer, default=100) # Global Limit: How many times total this code can be used in the shop
    max_usage_per_user = Column(Integer, default=1) # User Limit: How many times a SINGLE identified customer can use this code
    
    usage_count = Column(Integer, default=0) # Real-time counter of total successful redemptions
    
    is_stackable = Column(Boolean, default=False) # Flag to allow/block combination with other promos
    eligibility_type = Column(Enum(EligibilityType), default=EligibilityType.all) # Filtering: VIP, NEW, or INACTIVE customers only
    
    status = Column(String(20), default="active") # Authorization Pulse: active, blocked, or expired
    
    # Mandatory Registry Metadata
    is_active = Column(Integer, default=1) # Soft deletion flag for registry cleanup
    created_at = Column(DateTime, default=get_ist_now) # Auto-timestamp: Record creation
    updated_at = Column(DateTime, default=get_ist_now, onupdate=get_ist_now) # Auto-timestamp: Last state modification

    # Relationships
    usages = relationship("CouponUsage", back_populates="coupon")


class CouponUsage(Base):
    __tablename__ = "coupon_usages"

    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id")) # Reference to the parent voucher protocol
    customer_id = Column(Integer, ForeignKey("customers.id")) # Reference to the identified client who redeemed it
    order_id = Column(Integer, nullable=True) # Link to the specific transactional audit (if applicable)
    
    discount_amount = Column(Float) # The specific financial benefit (₹ saved) in this unique event
    
    redeemed_at = Column(DateTime, default=get_ist_now) # The precise minute of protocol authorization
    
    # Mandatory Registry Metadata
    is_active = Column(Integer, default=1) # Soft deletion flag
    created_at = Column(DateTime, default=get_ist_now) # Auto-timestamp: Record creation
    updated_at = Column(DateTime, default=get_ist_now, onupdate=get_ist_now) # Auto-timestamp: Last state modification
    
    # Relationships
    coupon = relationship("Coupon", back_populates="usages")
    customer = relationship("Customer")
