from pydantic import BaseModel, field_validator


class RedeemRequest(BaseModel):
    phone: str
    points_to_redeem: int

    @field_validator("points_to_redeem")
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("points_to_redeem must be greater than 0")
        return v
