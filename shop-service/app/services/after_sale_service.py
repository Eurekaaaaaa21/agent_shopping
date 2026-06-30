from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.after_sale import AfterSaleRequest
from app.models.order import Order
from app.core.exceptions import BusinessException


async def create_after_sale(db: AsyncSession, user_id: int, order_id: int, type_: str, reason: Optional[str] = None) -> AfterSaleRequest:
    """发起售后"""
    if type_ not in ("refund", "return"):
        raise BusinessException("售后类型只能是 refund 或 return")

    order_result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.status != "paid":
        raise BusinessException("仅已支付订单可申请售后")

    request = AfterSaleRequest(
        order_id=order_id,
        user_id=user_id,
        type=type_,
        reason=reason,
        status="pending",
    )
    db.add(request)
    await db.flush()
    await db.refresh(request)
    return request


async def get_user_after_sales(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20):
    query = select(AfterSaleRequest).where(AfterSaleRequest.user_id == user_id).order_by(AfterSaleRequest.id.desc())
    count_query = select(func.count()).select_from(AfterSaleRequest).where(AfterSaleRequest.user_id == user_id)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    requests = result.scalars().all()
    total = (await db.execute(count_query)).scalar()
    return requests, total


async def get_all_after_sales_admin(db: AsyncSession, status_filter: Optional[str] = None, page: int = 1, page_size: int = 20):
    query = select(AfterSaleRequest).order_by(AfterSaleRequest.id.desc())
    count_query = select(func.count()).select_from(AfterSaleRequest)
    if status_filter:
        query = query.where(AfterSaleRequest.status == status_filter)
        count_query = count_query.where(AfterSaleRequest.status == status_filter)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    requests = result.scalars().all()
    total = (await db.execute(count_query)).scalar()
    return requests, total


async def review_after_sale(db: AsyncSession, request_id: int, action: str, admin_note: Optional[str] = None) -> AfterSaleRequest:
    """管理员审核售后"""
    if action not in ("approved", "rejected", "completed"):
        raise BusinessException("操作类型只能是 approved/rejected/completed")

    result = await db.execute(select(AfterSaleRequest).where(AfterSaleRequest.id == request_id).with_for_update())
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="售后申请不存在")

    # 状态流转校验
    if action == "approved" and request.status != "pending":
        raise BusinessException("仅待处理的申请可以审核通过")
    if action == "rejected" and request.status != "pending":
        raise BusinessException("仅待处理的申请可以驳回")
    if action == "completed" and request.status != "approved":
        raise BusinessException("仅已通过的申请可以确认完成")

    request.status = action
    if admin_note:
        request.admin_note = admin_note

    await db.flush()
    await db.refresh(request)
    return request


async def get_user_after_sales_internal(db: AsyncSession, user_id: int):
    """内部接口：返回用户所有售后"""
    result = await db.execute(
        select(AfterSaleRequest).where(AfterSaleRequest.user_id == user_id).order_by(AfterSaleRequest.id.desc())
    )
    requests = result.scalars().all()
    return [
        {
            "id": r.id, "order_id": r.order_id, "type": r.type,
            "reason": r.reason, "status": r.status,
            "admin_note": r.admin_note,
            "created_at": str(r.created_at) if r.created_at else None,
            "updated_at": str(r.updated_at) if r.updated_at else None,
        }
        for r in requests
    ]
