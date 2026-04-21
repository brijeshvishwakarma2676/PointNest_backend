from pydantic import BaseModel, ConfigDict, model_validator
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

    @model_validator(mode='after')
    def compute_status(self):
        from app.utils.datetime_utils import get_ist_now
        
        if self.status == 'draft':
            return self
            
        now = get_ist_now()
        
        if self.start_date and now < self.start_date:
            self.status = "upcoming"
        elif self.usage_count >= self.max_usage_global:
            self.status = "exhausted"
        elif self.expiry_date and now > self.expiry_date:
            self.status = "expired"
        else:
            self.status = "active"
            
        return self

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
    page: int
    size: int
    items: List[CouponResponse]

class CouponValidateRequest(BaseModel):
    code: str

class CouponValidateResponse(BaseModel):
    valid: bool
    coupon: Optional[CouponResponse] = None
    message: str

class CouponRedeemRequest(BaseModel):
    code: str
    customer_phone: str
    order_amount: float
