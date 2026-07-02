from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import joinedload

from app.models.browsing_history import BrowsingHistory
from app.models.product import Product


async def record_view(db: AsyncSession, user_id: int, product_id: int) -> BrowsingHistory:
    """记录/更新浏览历史（UPSERT：同一用户同一商品只保留最新一次浏览）"""
    result = await db.execute(
        select(BrowsingHistory).where(
            BrowsingHistory.user_id == user_id,
            BrowsingHistory.product_id == product_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        # 更新浏览时间
        existing.viewed_at = func.now()
        await db.flush()
        await db.refresh(existing)
        return existing
    else:
        history = BrowsingHistory(user_id=user_id, product_id=product_id)
        db.add(history)
        await db.flush()
        await db.refresh(history)
        return history


async def get_history(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 12
) -> Tuple[List[BrowsingHistory], int]:
    """分页获取浏览历史（含商品信息，按浏览时间倒序）"""
    # 总数
    count_result = await db.execute(
        select(func.count()).select_from(BrowsingHistory).where(
            BrowsingHistory.user_id == user_id
        )
    )
    total = count_result.scalar() or 0

    # 分页查询（LEFT JOIN 商品表获取商品信息）
    result = await db.execute(
        select(BrowsingHistory)
        .options(joinedload(BrowsingHistory.product))
        .where(BrowsingHistory.user_id == user_id)
        .order_by(BrowsingHistory.viewed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.unique().scalars().all())
    return items, total


async def delete_history_item(db: AsyncSession, user_id: int, history_id: int) -> int:
    """删除单条浏览记录，返回删除行数"""
    result = await db.execute(
        delete(BrowsingHistory).where(
            BrowsingHistory.id == history_id,
            BrowsingHistory.user_id == user_id,
        )
    )
    await db.flush()
    return result.rowcount


async def clear_history(db: AsyncSession, user_id: int) -> int:
    """清空用户全部浏览记录，返回删除行数"""
    result = await db.execute(
        delete(BrowsingHistory).where(BrowsingHistory.user_id == user_id)
    )
    await db.flush()
    return result.rowcount
