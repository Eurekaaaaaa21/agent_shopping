from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.core.deps import get_current_user_id, require_admin
from app.schemas.after_sale import AfterSaleCreate, AfterSaleReview, AfterSaleOut
from app.schemas.common import ResponseBase
from app.services import after_sale_service

router = APIRouter(prefix="/after-sales", tags=["售后"])


@router.post("")
async def create_after_sale(data: AfterSaleCreate, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    request = await after_sale_service.create_after_sale(db, user_id, data.order_id, data.type, data.reason)
    return ResponseBase(data=AfterSaleOut.model_validate(request).model_dump(), message="售后申请已提交")


@router.get("")
async def list_after_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    requests, total = await after_sale_service.get_user_after_sales(db, user_id, page, page_size)
    items = [AfterSaleOut.model_validate(r).model_dump() for r in requests]
    return ResponseBase(data={"items": items, "total": total, "page": page, "page_size": page_size})


# 管理员接口
admin_after_sale_router = APIRouter(prefix="/admin/after-sales", tags=["管理员-售后"])


@admin_after_sale_router.get("")
async def admin_list_after_sales(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    auth: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    requests, total = await after_sale_service.get_all_after_sales_admin(db, status, page, page_size)
    items = [AfterSaleOut.model_validate(r).model_dump() for r in requests]
    return ResponseBase(data={"items": items, "total": total, "page": page, "page_size": page_size})


@admin_after_sale_router.post("/{request_id}/review")
async def review_after_sale(request_id: int, data: AfterSaleReview, auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    request = await after_sale_service.review_after_sale(db, request_id, data.action, data.admin_note)
    return ResponseBase(data=AfterSaleOut.model_validate(request).model_dump(), message="审核完成")
