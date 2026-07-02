from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AddressCreate(BaseModel):
    receiver_name: str = Field(..., min_length=1, max_length=50, description="收货人姓名")
    phone: str = Field(..., min_length=1, max_length=20, description="收货人电话")
    province: str = Field(..., min_length=1, max_length=50, description="省份")
    city: str = Field(..., min_length=1, max_length=50, description="城市")
    district: str = Field(..., min_length=1, max_length=50, description="区县")
    detail: str = Field(..., min_length=1, max_length=200, description="详细地址")
    is_default: bool = Field(default=False, description="是否设为默认地址")


class AddressUpdate(BaseModel):
    receiver_name: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)
    province: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=50)
    district: Optional[str] = Field(default=None, max_length=50)
    detail: Optional[str] = Field(default=None, max_length=200)
    is_default: Optional[bool] = None


class AddressOut(BaseModel):
    id: int
    user_id: int
    receiver_name: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    is_default: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
