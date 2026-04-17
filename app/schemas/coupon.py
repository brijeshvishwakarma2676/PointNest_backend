from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class CouponType(str, Enum):
    percentage = "percentage"
    fixed = "fixed"

class EligibilityType(str, Enum):
    all = "all"
    vip = "vip"
    new = "new"
    inactive = "inactive"

class CouponBase(BaseModel):
    code: str
    type: CouponType = CouponType.percentage
    value: float
    max_discount_cap: Optional[float] = None
    min_order_value: float = 0.0
    start_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    max_usage_global: int = 100
    max_usage_per_user: int = 1
    is_stackable: bool = False
    eligibility_type: EligibilityType = EligibilityType.all

class CouponCreate(CouponBase):
    pass

class CouponUpdate(BaseModel):
    is_active: Optional[int] = None
    status: Optional[str] = None

class CouponResponse(CouponBase):
    id: int
    shop_id: int
    usage_count: int
    status: str
    is_active: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CouponUsageResponse(BaseModel):
    id: int
    coupon_id: int
    customer_id: int
    order_id: Optional[int] = None
    discount_amount: float
    redeemed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CouponListResponse(BaseModel):
    total: int
    items: List[CouponResponse]
