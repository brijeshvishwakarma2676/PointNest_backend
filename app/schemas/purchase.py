from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PurchaseCreate(BaseModel):
    amount: float
    phone: str
    coupon_code: Optional[str] = None
    points_to_redeem: int = 0

class PurchaseResponse(BaseModel):
    id: int
    amount: float
    points_earned: int
    created_at: datetime
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    coupon_code: Optional[str] = None
    coupon_usage_id: Optional[int] = None
    redemption_id: Optional[int] = None
    points_redeemed: int = 0
    coupon_discount: float = 0.0
    points_discount: float = 0.0
    payable_amount: float

    class Config:
        from_attributes = True

