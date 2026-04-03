from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class RedeemRequest(BaseModel):
    phone: str
    points_to_redeem: int

    @field_validator("points_to_redeem")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("points_to_redeem must be greater than 0")
        return v


class RedemptionResponse(BaseModel):
    id: int
    shop_id: int
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    points_used: int
    amount_discounted: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
