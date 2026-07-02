from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BrowsingHistoryCreate(BaseModel):
    product_id: int = Field(..., ge=1, description="商品ID")


class BrowsingHistoryOut(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_image: Optional[str] = None
    product_price: Optional[float] = None
    product_status: Optional[str] = None
    viewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
