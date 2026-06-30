from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LogisticsNode(BaseModel):
    status: str
    description: str
    time: str


class LogisticsOut(BaseModel):
    id: int
    order_id: int
    status: str
    tracking_info: Optional[list[LogisticsNode]] = None
    estimated_delivery: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
