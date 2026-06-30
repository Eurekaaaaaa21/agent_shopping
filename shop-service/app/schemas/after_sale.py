from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AfterSaleCreate(BaseModel):
    order_id: int
    type: str  # refund / return
    reason: Optional[str] = None


class AfterSaleReview(BaseModel):
    action: str  # approved / rejected / completed
    admin_note: Optional[str] = None


class AfterSaleOut(BaseModel):
    id: int
    order_id: int
    user_id: int
    type: str
    reason: Optional[str] = None
    status: str
    admin_note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
