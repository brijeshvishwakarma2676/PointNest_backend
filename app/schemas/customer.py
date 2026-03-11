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


class CustomerListRequest(BaseModel):
    page: int = 1
    size: int = 10
    search_query: str | None = None

class CustomerUpdate(BaseModel):
    id: int
    name: str
    phone: str | None = None
    email: str | None = None

    @field_validator("email", mode="before")
    def check_contact(cls, v, values):
        if not v and not values.get("phone"):
            raise ValueError("phone or email required")
        return v
