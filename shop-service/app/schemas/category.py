from pydantic import BaseModel
from typing import Optional


class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


class CategoryTree(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    children: list["CategoryTree"] = []

    class Config:
        from_attributes = True
