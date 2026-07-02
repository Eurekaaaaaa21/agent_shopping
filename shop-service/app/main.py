import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.exceptions import BusinessException, business_exception_handler, general_exception_handler
from app.core.middleware import RequestIdMiddleware
from app.db.session import engine, Base, async_session_factory, init_db
from app.db.redis import init_redis, close_redis

settings = get_settings()

# 导入所有模型以确保 Base.metadata 包含所有表
from app.models import *  # noqa: F401,F403

from app.api.user_router import router as user_router
from app.api.product_router import router as product_router, category_router
from app.api.cart_router import router as cart_router
from app.api.order_router import router as order_router, admin_order_router
from app.api.logistics_router import router as logistics_router, admin_logistics_router
from app.api.after_sale_router import router as after_sale_router, admin_after_sale_router
from app.api.internal_router import router as internal_router
from app.api.address_router import router as address_router

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.order_service import cancel_timeout_orders

# 配置日志
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# APScheduler
scheduler = AsyncIOScheduler()


async def timeout_order_job():
    """定时任务：超时订单自动取消"""
    try:
        count = await cancel_timeout_orders(settings.ORDER_TIMEOUT_MINUTES)
        if count > 0:
            logger.info(f"超时取消处理完成，取消 {count} 个订单")
    except Exception as e:
        logger.error(f"超时取消任务执行失败: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    logger.info("Starting Shop Service...")

    # 初始化 Redis
    await init_redis()

    # 初始化 SQLite 性能优化
    await init_db()

    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    # 初始化管理员账号
    await _init_admin()

    # 启动定时任务
    scheduler.add_job(timeout_order_job, "interval", minutes=5, id="cancel_timeout_orders")
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # 关闭时
    scheduler.shutdown()
    await close_redis()
    await engine.dispose()
    logger.info("Shop Service stopped")


async def _init_admin():
    """初始化默认管理员账号"""
    from app.models.user import User
    from app.core.security import hash_password
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == "admin@shop.com"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin@shop.com",
                nickname="管理员",
                hashed_password=hash_password("admin123"),
                role="admin",
                shipping_address="系统默认地址",
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin created: admin@shop.com / admin123")
        else:
            logger.info("Admin account already exists")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID 中间件
app.add_middleware(RequestIdMiddleware)

# 异常处理
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(user_router, prefix="/api/shop")
app.include_router(product_router, prefix="/api/shop")
app.include_router(category_router, prefix="/api/shop")
app.include_router(cart_router, prefix="/api/shop")
app.include_router(order_router, prefix="/api/shop")
app.include_router(admin_order_router, prefix="/api/shop")
app.include_router(logistics_router, prefix="/api/shop")
app.include_router(admin_logistics_router, prefix="/api/shop")
app.include_router(after_sale_router, prefix="/api/shop")
app.include_router(admin_after_sale_router, prefix="/api/shop")
app.include_router(internal_router, prefix="/api/shop")
app.include_router(address_router, prefix="/api/shop")


# 健康检查
@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/", tags=["首页"])
async def index():
    return FileResponse("app/static/templates/index.html")


@app.get("/admin", tags=["管理后台"])
async def admin_page():
    return FileResponse("app/static/templates/admin.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=settings.DEBUG)
