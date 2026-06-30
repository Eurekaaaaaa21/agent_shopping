from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.core.deps import get_current_user_id
from app.schemas.common import ResponseBase
from app.services import order_service, logistics_service, after_sale_service, product_service
from app.models.order import OrderItem

router = APIRouter(prefix="/internal", tags=["内部接口"])


@router.get("/orders")
async def internal_orders(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """内部接口：查询当前用户订单列表（ai-service 调用）"""
    orders, total = await order_service.get_user_orders(db, user_id)
    items = []
    for o in orders:
        items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == o.id))
        order_items = items_result.scalars().all()
        items.append({
            "id": o.id,
            "total_amount": float(o.total_amount),
            "status": o.status,
            "shipping_address": o.shipping_address,
            "created_at": str(o.created_at) if o.created_at else None,
            "items": [
                {
                    "product_id": i.product_id,
                    "product_name": i.product_name,
                    "product_price": float(i.product_price),
                    "quantity": i.quantity,
                    "subtotal": float(i.subtotal),
                }
                for i in order_items
            ],
        })
    return ResponseBase(data=items)


@router.get("/logistics")
async def internal_logistics(
    order_id: int = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """内部接口：查询物流（ai-service 调用）"""
    data = await logistics_service.get_logistics_by_order_internal(db, order_id, user_id)
    if not data:
        return ResponseBase(data=None, message="暂无物流信息")
    return ResponseBase(data=data)


@router.get("/after-sales")
async def internal_after_sales(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """内部接口：查询售后（ai-service 调用）"""
    data = await after_sale_service.get_user_after_sales_internal(db, user_id)
    return ResponseBase(data=data)


@router.get("/products/search")
async def internal_products_search(
    keyword: str = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """内部接口：搜索商品（ai-service 调用）"""
    data = await product_service.search_products_internal(db, keyword)
    return ResponseBase(data=data)
