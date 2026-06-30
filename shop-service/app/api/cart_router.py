from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user_id
from app.core.exceptions import BusinessException
from app.schemas.cart import CartItemAdd, CartItemUpdate
from app.schemas.common import ResponseBase
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["购物车"])


@router.get("")
async def get_cart(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    items, total = await cart_service.get_cart(db, user_id)
    return ResponseBase(data={"items": items, "total_amount": total})


@router.post("")
async def add_to_cart(data: CartItemAdd, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await cart_service.add_to_cart(db, user_id, data.product_id, data.quantity)
    items, total = await cart_service.get_cart(db, user_id)
    return ResponseBase(data={"items": items, "total_amount": total}, message="已加入购物车")


@router.put("/{item_id}")
async def update_cart_item(item_id: int, data: CartItemUpdate, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await cart_service.update_cart_item(db, item_id, user_id, data.quantity)
    items, total = await cart_service.get_cart(db, user_id)
    return ResponseBase(data={"items": items, "total_amount": total})


@router.delete("/{item_id}")
async def delete_cart_item(item_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await cart_service.delete_cart_item(db, item_id, user_id)
    items, total = await cart_service.get_cart(db, user_id)
    return ResponseBase(data={"items": items, "total_amount": total}, message="已移除")
