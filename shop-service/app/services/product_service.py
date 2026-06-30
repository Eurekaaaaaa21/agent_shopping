from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.category import Category
from app.db.redis import cache_get, cache_set, cache_delete, cache_delete_pattern


async def _get_category_descendants(db: AsyncSession, category_id: int) -> List[int]:
    """递归获取分类及其所有子孙分类的 ID"""
    all_ids = [category_id]
    result = await db.execute(select(Category).where(Category.parent_id == category_id))
    children = result.scalars().all()
    for child in children:
        sub_ids = await _get_category_descendants(db, child.id)
        all_ids.extend(sub_ids)
    return all_ids


async def get_products(
    db: AsyncSession,
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """C端浏览商品：仅 on_sale，分类筛选含子分类"""
    offset = (page - 1) * page_size
    query = select(Product).where(Product.status == "on_sale")
    count_query = select(func.count()).select_from(Product).where(Product.status == "on_sale")

    if category_id:
        # 递归获取该分类及所有子孙分类 ID
        all_category_ids = await _get_category_descendants(db, category_id)
        query = query.where(Product.category_id.in_(all_category_ids))
        count_query = count_query.where(Product.category_id.in_(all_category_ids))

    if keyword:
        filter_cond = Product.name.ilike(f"%{keyword}%")
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    query = query.order_by(Product.id.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    products = result.scalars().all()
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    return products, total


async def get_hot_products(db: AsyncSession):
    """热门商品列表（带缓存）"""
    from app.core.config import get_settings
    settings = get_settings()

    cached = await cache_get("hot_products")
    if cached:
        return cached

    result = await db.execute(
        select(Product)
        .where(Product.status == "on_sale")
        .order_by(Product.id.desc())
        .limit(10)
    )
    products = result.scalars().all()
    data = [
        {
            "id": p.id, "name": p.name, "price": float(p.price),
            "image_url": p.image_url, "stock": p.stock, "category_id": p.category_id,
        }
        for p in products
    ]
    await cache_set("hot_products", data, settings.CACHE_TTL_HOT_PRODUCTS)
    return data


async def get_product_detail(db: AsyncSession, product_id: int):
    """商品详情（带缓存）"""
    from app.core.config import get_settings
    settings = get_settings()

    cache_key = f"product_detail:{product_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        return None

    data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "image_url": product.image_url,
        "stock": product.stock,
        "category_id": product.category_id,
        "status": product.status,
        "created_at": str(product.created_at) if product.created_at else None,
    }
    await cache_set(cache_key, data, settings.CACHE_TTL_PRODUCT_DETAIL)
    return data


async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def get_all_products_admin(db: AsyncSession, page: int = 1, page_size: int = 20):
    """管理员查看所有商品（含下架）"""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Product).order_by(Product.id.desc()).offset(offset).limit(page_size)
    )
    products = result.scalars().all()
    total_result = await db.execute(select(func.count()).select_from(Product))
    total = total_result.scalar()
    return products, total


async def create_product(db: AsyncSession, **kwargs) -> Product:
    product = Product(**kwargs)
    db.add(product)
    await db.flush()
    await db.refresh(product)
    # 清除热门商品缓存
    await cache_delete("hot_products")
    return product


async def update_product(db: AsyncSession, product_id: int, **kwargs) -> Product:
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    for key, value in kwargs.items():
        if value is not None:
            setattr(product, key, value)
    await db.flush()
    await db.refresh(product)
    # 清除缓存
    await cache_delete(f"product_detail:{product_id}")
    await cache_delete("hot_products")
    return product


async def toggle_product_status(db: AsyncSession, product_id: int) -> Product:
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    product.status = "off_sale" if product.status == "on_sale" else "on_sale"
    await db.flush()
    await db.refresh(product)
    await cache_delete(f"product_detail:{product_id}")
    await cache_delete("hot_products")
    return product


async def search_products_internal(db: AsyncSession, keyword: str):
    """内部接口：搜索商品（校验 JWT 后调用）"""
    result = await db.execute(
        select(Product)
        .where(Product.name.ilike(f"%{keyword}%"))
        .limit(20)
    )
    products = result.scalars().all()
    return [
        {
            "id": p.id, "name": p.name, "price": float(p.price),
            "description": p.description, "image_url": p.image_url,
            "stock": p.stock, "status": p.status,
        }
        for p in products
    ]
