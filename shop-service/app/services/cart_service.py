from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.cart import CartItem
from app.models.product import Product
from app.core.exceptions import BusinessException


async def get_cart(db: AsyncSession, user_id: int):
    """获取购物车（JOIN 商品信息）"""
    result = await db.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.id)
    )
    rows = result.all()
    items = []
    total = 0.0
    for cart_item, product in rows:
        subtotal = float(product.price) * cart_item.quantity
        total += subtotal
        items.append({
            "id": cart_item.id,
            "product_id": product.id,
            "product_name": product.name,
            "product_price": float(product.price),
            "product_image_url": product.image_url,
            "quantity": cart_item.quantity,
            "subtotal": round(subtotal, 2),
        })
    return items, round(total, 2)


async def add_to_cart(db: AsyncSession, user_id: int, product_id: int, quantity: int = 1) -> CartItem:
    """UPSERT 购物车"""
    product = await db.execute(select(Product).where(Product.id == product_id))
    p = product.scalar_one_or_none()
    if not p or p.status != "on_sale":
        raise BusinessException("商品不存在或已下架")
    if p.stock < quantity:
        raise BusinessException("库存不足")

    existing = await db.execute(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    )
    cart_item = existing.scalar_one_or_none()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.add(cart_item)
    await db.flush()
    await db.refresh(cart_item)
    return cart_item


async def update_cart_item(db: AsyncSession, cart_item_id: int, user_id: int, quantity: int) -> CartItem:
    if quantity <= 0:
        raise BusinessException("数量必须大于0")
    result = await db.execute(
        select(CartItem).where(CartItem.id == cart_item_id, CartItem.user_id == user_id)
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="购物车项不存在")
    cart_item.quantity = quantity
    await db.flush()
    await db.refresh(cart_item)
    return cart_item


async def delete_cart_item(db: AsyncSession, cart_item_id: int, user_id: int) -> None:
    result = await db.execute(
        select(CartItem).where(CartItem.id == cart_item_id, CartItem.user_id == user_id)
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="购物车项不存在")
    await db.delete(cart_item)


async def clear_cart(db: AsyncSession, user_id: int) -> None:
    result = await db.execute(select(CartItem).where(CartItem.user_id == user_id))
    items = result.scalars().all()
    for item in items:
        await db.delete(item)
