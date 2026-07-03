from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user_id
from app.schemas.browsing_history import BrowsingHistoryCreate, BrowsingHistoryOut
from app.schemas.common import ResponseBase
from app.services import browsing_history_service

router = APIRouter(prefix="/users/me/history", tags=["浏览历史"])


@router.post("")
async def record_browsing(
    data: BrowsingHistoryCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """记录浏览历史（打开商品详情时调用，同商品会更新浏览时间而非重复记录）"""
    await browsing_history_service.record_view(db, user_id, data.product_id)
    return ResponseBase(message="已记录")


@router.get("")
async def list_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取浏览历史列表（含商品信息，按浏览时间倒序）"""
    items, total = await browsing_history_service.get_history(db, user_id, page, page_size)
    data = []
    for h in items:
        d = BrowsingHistoryOut.model_validate(h).model_dump()
        if h.product:
            d["product_name"] = h.product.name
            d["product_image"] = h.product.image_url
            d["product_price"] = h.product.price
            d["product_status"] = h.product.status
        data.append(d)

    return ResponseBase(
        data={
            "items": data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.delete("/{history_id}")
async def delete_history_item(
    history_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除单条浏览记录"""
    count = await browsing_history_service.delete_history_item(db, user_id, history_id)
    if count == 0:
        return ResponseBase(code=404, message="记录不存在")
    return ResponseBase(message="已删除")


@router.delete("")
async def clear_history(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """清空全部浏览记录"""
    count = await browsing_history_service.clear_history(db, user_id)
    return ResponseBase(message=f"已清空 {count} 条记录")
