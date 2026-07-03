from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    shipping_address: Optional[str] = None  # 为空时使用用户默认地址


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: float
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    shipping_address: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    items: list[OrderItemOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class OrderDetail(BaseModel):
    order: OrderOut
    items: list[OrderItemOut]


class PaymentOut(BaseModel):
    id: int
    order_id: int
    amount: float
    method: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
