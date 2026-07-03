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
async def internal_orders(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """内部接口：查询当前用户订单列表（ai-service 调用）"""
    orders, total = await order_service.get_user_orders(db, user_id, status, page, page_size)
    items = []
    for o in orders:
        items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == o.id))
        order_items = items_result.scalars().all()
        items.append({
            "id": o.id,
            "total_amount": float(o.total_amount),
            "status": o.status,
            "shipping_address": o.shipping_address,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            "cancelled_at": o.cancelled_at.isoformat() if o.cancelled_at else None,
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
    return ResponseBase(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/orders/{order_id}")
async def internal_order_detail(
    order_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """内部接口：单笔订单详情（ai-service 调用），复用已有归属校验"""
    order, items = await order_service.get_order_detail(db, order_id, user_id)
    return ResponseBase(data={
        "order": {
            "id": order.id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "shipping_address": order.shipping_address,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
        },
        "items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "product_name": i.product_name,
                "product_price": float(i.product_price),
                "quantity": i.quantity,
                "subtotal": float(i.subtotal),
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ],
    })


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
