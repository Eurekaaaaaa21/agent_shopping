from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.category import Category
from app.models.product import Product
from app.db.redis import cache_get, cache_set, cache_delete


async def get_category_tree(db: AsyncSession):
    """获取分类树（带缓存）"""
    from app.core.config import get_settings
    settings = get_settings()

    cached = await cache_get("category_tree")
    if cached:
        return cached

    result = await db.execute(select(Category).order_by(Category.id))
    categories = result.scalars().all()

    tree = _build_tree([{"id": c.id, "name": c.name, "parent_id": c.parent_id} for c in categories])
    await cache_set("category_tree", tree, settings.CACHE_TTL_CATEGORY_TREE)
    return tree


def _build_tree(categories: list, parent_id: Optional[int] = None) -> list:
    tree = []
    for cat in categories:
        if cat["parent_id"] == parent_id:
            node = {"id": cat["id"], "name": cat["name"], "parent_id": cat["parent_id"], "children": []}
            node["children"] = _build_tree(categories, cat["id"])
            tree.append(node)
    return tree


async def create_category(db: AsyncSession, name: str, parent_id: Optional[int] = None) -> Category:
    category = Category(name=name, parent_id=parent_id)
    db.add(category)
    await db.flush()
    await db.refresh(category)
    await cache_delete("category_tree")
    return category


async def update_category(db: AsyncSession, category_id: int, name: Optional[str] = None, parent_id: Optional[int] = None) -> Category:
    category = await get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    if name is not None:
        category.name = name
    if parent_id is not None:
        category.parent_id = parent_id
    await db.flush()
    await db.refresh(category)
    await cache_delete("category_tree")
    return category


async def delete_category(db: AsyncSession, category_id: int) -> None:
    category = await get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    # 检查是否有商品引用
    result = await db.execute(select(func.count()).select_from(Product).where(Product.category_id == category_id))
    count = result.scalar()
    if count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该分类下有商品，无法删除")
    # 检查是否有子分类
    children_result = await db.execute(select(func.count()).select_from(Category).where(Category.parent_id == category_id))
    children_count = children_result.scalar()
    if children_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该分类下有子分类，无法删除")
    await db.delete(category)
    await cache_delete("category_tree")


async def get_category_by_id(db: AsyncSession, category_id: int) -> Optional[Category]:
    result = await db.execute(select(Category).where(Category.id == category_id))
    return result.scalar_one_or_none()


async def get_all_categories(db: AsyncSession):
    result = await db.execute(select(Category).order_by(Category.id))
    return result.scalars().all()
