from pydantic import BaseModel, model_validator


class CustomerCreate(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None

    @model_validator(mode="after")
    def check_contact(self) -> "CustomerCreate":
        if not self.phone and not self.email:
            raise ValueError("phone or email required")
        return self


class CustomerListRequest(BaseModel):
    page: int = 1
    size: int = 10
    search_query: str | None = None

class CustomerUpdate(BaseModel):
    id: int
    name: str
    phone: str | None = None
    email: str | None = None

    @model_validator(mode="after")
    def check_contact(self) -> "CustomerUpdate":
        if not self.phone and not self.email:
            raise ValueError("phone or email required")
        return self
