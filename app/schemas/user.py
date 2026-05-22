from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    shop_name: str
    owner_name: str
    email: str
    phone: str


class UserRegister(UserBase):
    password: str


class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class GoogleLoginRequest(BaseModel):
    id_token: str


