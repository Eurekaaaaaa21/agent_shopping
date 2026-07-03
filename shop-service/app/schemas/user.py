from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    nickname: str
    password: str
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    shipping_address: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    email: str
    nickname: str
    role: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    shipping_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
