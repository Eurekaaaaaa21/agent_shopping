from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user_id, require_admin
from app.core.exceptions import BusinessException
from app.schemas.common import ResponseBase
from app.services import logistics_service

router = APIRouter(prefix="/logistics", tags=["物流"])


@router.get("/{order_id}")
async def get_logistics(order_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    data = await logistics_service.get_logistics_by_order(db, order_id, user_id)
    return ResponseBase(data=data)


# 管理员推进物流
admin_logistics_router = APIRouter(prefix="/admin/logistics", tags=["管理员-物流"])


@admin_logistics_router.post("/{order_id}/advance")
async def advance_status(order_id: int, auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    record = await logistics_service.advance_logistics_status(db, order_id)
    return ResponseBase(data={"order_id": record.order_id, "status": record.status}, message="物流状态已更新")
