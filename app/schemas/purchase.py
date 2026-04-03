from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PurchaseBase(BaseModel):
    amount: int
    points_earned: int

class PurchaseCreate(PurchaseBase):
    phone: str

class PurchaseResponse(PurchaseBase):
    id: int
    created_at: datetime
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None

    class Config:
        from_attributes = True
