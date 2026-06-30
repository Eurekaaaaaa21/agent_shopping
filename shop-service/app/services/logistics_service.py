import json
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.logistics import LogisticsRecord
from app.models.order import Order
from app.core.exceptions import BusinessException

STATUS_FLOW = ["picked_up", "in_transit", "out_for_delivery", "delivered"]
STATUS_DESCRIPTIONS = {
    "picked_up": "包裹已揽收",
    "in_transit": "包裹运输中",
    "out_for_delivery": "包裹派送中",
    "delivered": "包裹已签收",
}


async def get_logistics_by_order(db: AsyncSession, order_id: int, user_id: int):
    """用户查询物流"""
    # 先校验订单归属
    order_result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    result = await db.execute(select(LogisticsRecord).where(LogisticsRecord.order_id == order_id))
    record = result.scalar_one_or_none()
    if not record:
        raise BusinessException("暂无物流信息")

    tracking_info = json.loads(record.tracking_info) if record.tracking_info else []
    return {
        "id": record.id,
        "order_id": record.order_id,
        "status": record.status,
        "tracking_info": tracking_info,
        "estimated_delivery": record.estimated_delivery,
    }


async def get_logistics_by_order_internal(db: AsyncSession, order_id: int, user_id: int):
    """内部接口调用：校验订单归属后返回物流"""
    order_result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    order = order_result.scalar_one_or_none()
    if not order:
        return None

    result = await db.execute(select(LogisticsRecord).where(LogisticsRecord.order_id == order_id))
    record = result.scalar_one_or_none()
    if not record:
        return None

    tracking_info = json.loads(record.tracking_info) if record.tracking_info else []
    return {
        "order_id": record.order_id,
        "order_status": order.status,
        "logistics_status": record.status,
        "tracking_info": tracking_info,
        "estimated_delivery": record.estimated_delivery,
    }


async def advance_logistics_status(db: AsyncSession, order_id: int):
    """管理员推进物流状态"""
    result = await db.execute(select(LogisticsRecord).where(LogisticsRecord.order_id == order_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物流记录不存在")

    current_index = STATUS_FLOW.index(record.status) if record.status in STATUS_FLOW else -1
    if current_index >= len(STATUS_FLOW) - 1:
        raise BusinessException("物流已到达最终状态")

    new_status = STATUS_FLOW[current_index + 1]
    record.status = new_status

    tracking_info = json.loads(record.tracking_info) if record.tracking_info else []
    tracking_info.append({
        "status": new_status,
        "description": STATUS_DESCRIPTIONS[new_status],
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    })
    record.tracking_info = json.dumps(tracking_info, ensure_ascii=False)

    await db.flush()
    await db.refresh(record)
    return record
