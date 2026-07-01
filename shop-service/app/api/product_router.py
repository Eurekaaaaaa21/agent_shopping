from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.core.deps import get_current_user_id, require_admin
from app.core.exceptions import BusinessException
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut, ProductListItem
from app.schemas.common import ResponseBase
from app.services import product_service, category_service

router = APIRouter(prefix="/products", tags=["商品"])


@router.get("/hot")
async def hot_products(db: AsyncSession = Depends(get_db)):
    data = await product_service.get_hot_products(db)
    return ResponseBase(data=data)


@router.get("/search")
async def search_products(
    keyword: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    products, total = await product_service.get_products(db, category_id, keyword, page, page_size)
    items = [
        {
            "id": p.id, "name": p.name, "price": float(p.price),
            "image_url": p.image_url, "stock": p.stock,
            "category_id": p.category_id, "status": p.status,
        }
        for p in products
    ]
    return ResponseBase(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/categories")
async def categories(db: AsyncSession = Depends(get_db)):
    tree = await category_service.get_category_tree(db)
    return ResponseBase(data=tree)


@router.get("/{product_id}")
async def product_detail(product_id: int, db: AsyncSession = Depends(get_db)):
    data = await product_service.get_product_detail(db, product_id)
    if not data:
        raise BusinessException("商品不存在")
    return ResponseBase(data=data)


# --- 以下为管理员接口 ---

@router.post("/admin")
async def create_product(data: ProductCreate, auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    product = await product_service.create_product(
        db, name=data.name, description=data.description, price=data.price,
        image_url=data.image_url, stock=data.stock, category_id=data.category_id,
        status="on_sale",
    )
    return ResponseBase(data=ProductOut.model_validate(product).model_dump())


@router.put("/admin/{product_id}")
async def update_product(product_id: int, data: ProductUpdate, auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    product = await product_service.update_product(db, product_id, **update_data)
    return ResponseBase(data=ProductOut.model_validate(product).model_dump())


@router.put("/admin/{product_id}/toggle-status")
async def toggle_status(product_id: int, auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    product = await product_service.toggle_product_status(db, product_id)
    return ResponseBase(data=ProductOut.model_validate(product).model_dump())


@router.get("/admin/list")
async def admin_list(auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db), page: int = 1, page_size: int = 20):
    products, total = await product_service.get_all_products_admin(db, page, page_size)
    return ResponseBase(data={
        "items": [ProductOut.model_validate(p).model_dump() for p in products],
        "total": total, "page": page, "page_size": page_size,
    })


# --- 分类管理（管理员） ---
category_router = APIRouter(prefix="/categories", tags=["分类"])


@category_router.post("/admin")
async def create_category(data: dict, auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    category = await category_service.create_category(db, name=data["name"], parent_id=data.get("parent_id"))
    return ResponseBase(data={"id": category.id, "name": category.name, "parent_id": category.parent_id})


@category_router.put("/admin/{category_id}")
async def update_category(category_id: int, data: dict, auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    category = await category_service.update_category(db, category_id, name=data.get("name"), parent_id=data.get("parent_id"))
    return ResponseBase(data={"id": category.id, "name": category.name, "parent_id": category.parent_id})


@category_router.delete("/admin/{category_id}")
async def delete_category(category_id: int, auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await category_service.delete_category(db, category_id)
    return ResponseBase(message="分类已删除")


@category_router.get("/admin/list")
async def admin_category_list(auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    categories = await category_service.get_all_categories(db)
    return ResponseBase(data=[{"id": c.id, "name": c.name, "parent_id": c.parent_id} for c in categories])
