from pydantic import BaseModel


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: float
    product_image_url: str | None
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    items: list[CartItemOut]
    total_amount: float
