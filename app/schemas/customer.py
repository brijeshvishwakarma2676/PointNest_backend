from pydantic import BaseModel, field_validator


class CustomerCreate(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None


    @field_validator("email", mode="before")
    def check_contact(cls, v, values):
        if not v and not values.get("phone"):
            raise ValueError("phone or email required")
        return v