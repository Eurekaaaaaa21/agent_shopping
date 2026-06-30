from pydantic import BaseModel
from typing import Optional, Any


class ResponseBase(BaseModel):
    code: int = 200
    message: str = "success"
    request_id: Optional[str] = None
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
