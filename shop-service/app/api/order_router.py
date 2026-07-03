from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, require_admin
from app.db.session import get_db
from app.schemas.common import ResponseBase
from app.schemas.order import OrderCreate, OrderItemOut, OrderOut, PaymentOut
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post("")
async def create_order(
    data: OrderCreate,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    order = await order_service.create_order(db, user_id, data.shipping_address)
    return ResponseBase(
        request_id=request.state.request_id,
        data={
            "id": order.id,
            "total_amount": float(order.total_amount),
            "status": order.status,
        },
        message="订单创建成功",
    )


@router.get("")
async def list_orders(
    request: Request,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    orders, total = await order_service.get_user_orders(db, user_id, status, page, page_size)
    items = [OrderOut.model_validate(o).model_dump() for o in orders]
    return ResponseBase(
        request_id=request.state.request_id,
        data={"items": items, "total": total, "page": page, "page_size": page_size},
    )


@router.get("/{order_id}")
async def order_detail(
    order_id: int,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    order, items = await order_service.get_order_detail(db, order_id, user_id)
    return ResponseBase(
        request_id=request.state.request_id,
        data={
            "order": OrderOut.model_validate(order).model_dump(),
            "items": [OrderItemOut.model_validate(i).model_dump() for i in items],
        },
    )


@router.post("/{order_id}/pay")
async def pay_order(
    order_id: int,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    payment = await order_service.pay_order(db, order_id, user_id)
    return ResponseBase(
        request_id=request.state.request_id,
        data=PaymentOut.model_validate(payment).model_dump(),
        message="支付成功",
    )


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await order_service.cancel_order(db, order_id, user_id)
    return ResponseBase(request_id=request.state.request_id, message="订单已取消")


# --- 管理员接口 ---
admin_order_router = APIRouter(prefix="/admin/orders", tags=["管理员-订单"])


@admin_order_router.get("")
async def admin_list_orders(
    request: Request,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    auth: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    orders, total = await order_service.get_all_orders_admin(db, status, page, page_size)
    items = [OrderOut.model_validate(o).model_dump() for o in orders]
    return ResponseBase(
        request_id=request.state.request_id,
        data={"items": items, "total": total, "page": page, "page_size": page_size},
    )
