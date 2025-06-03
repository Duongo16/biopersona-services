from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str
    rememberMe: bool = False

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    businessId: Optional[str] = None

class BusinessRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


