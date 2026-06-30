"""初始化演示数据脚本"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine, Base, async_session_factory
from app.models import *
from app.core.security import hash_password
from app.models.user import User
from app.models.category import Category
from app.models.product import Product


async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # 检查是否已有数据
        from sqlalchemy import select, func
        count = (await session.execute(select(func.count()).select_from(Product))).scalar()
        if count > 0:
            print("数据已存在，跳过初始化")
            return

        # 创建分类
        categories = [
            Category(name="电子产品"),
            Category(name="服装"),
            Category(name="食品"),
            Category(name="图书"),
            Category(name="手机", parent_id=1),
            Category(name="电脑", parent_id=1),
            Category(name="男装", parent_id=2),
            Category(name="女装", parent_id=2),
        ]
        for c in categories:
            session.add(c)
        await session.flush()

        # 创建商品
        products_data = [
            {"name": "iPhone 15 Pro Max", "description": "最新款苹果手机，A17 Pro芯片", "price": 9999.00, "image_url": "", "stock": 100, "category_id": 5, "status": "on_sale"},
            {"name": "MacBook Pro 16寸", "description": "M3 Max芯片，专业级笔记本", "price": 19999.00, "image_url": "", "stock": 50, "category_id": 6, "status": "on_sale"},
            {"name": "华为 Mate 60 Pro", "description": "麒麟芯片，卫星通话", "price": 6999.00, "image_url": "", "stock": 80, "category_id": 5, "status": "on_sale"},
            {"name": "Python编程从入门到实践", "description": "经典Python入门书籍", "price": 89.00, "image_url": "", "stock": 200, "category_id": 4, "status": "on_sale"},
            {"name": "优衣库男士T恤", "description": "纯棉舒适，多色可选", "price": 99.00, "image_url": "", "stock": 500, "category_id": 7, "status": "on_sale"},
            {"name": "三只松鼠坚果礼盒", "description": "混合坚果大礼包 1.5kg", "price": 128.00, "image_url": "", "stock": 300, "category_id": 3, "status": "on_sale"},
            {"name": "小米14 Ultra", "description": "徕卡光学镜头，骁龙8 Gen3", "price": 5999.00, "image_url": "", "stock": 60, "category_id": 5, "status": "on_sale"},
            {"name": "戴尔 XPS 15", "description": "Intel i9, RTX 4060", "price": 12999.00, "image_url": "", "stock": 30, "category_id": 6, "status": "on_sale"},
            {"name": "连衣裙 夏季新款", "description": "优雅碎花连衣裙", "price": 199.00, "image_url": "", "stock": 150, "category_id": 8, "status": "on_sale"},
            {"name": "良品铺子肉脯", "description": "猪肉脯 500g", "price": 59.90, "image_url": "", "stock": 400, "category_id": 3, "status": "on_sale"},
            {"name": "AirPods Pro 2", "description": "主动降噪，自适应通透模式", "price": 1899.00, "image_url": "", "stock": 120, "category_id": 1, "status": "on_sale"},
            {"name": "算法导论", "description": "计算机科学经典教材", "price": 128.00, "image_url": "", "stock": 100, "category_id": 4, "status": "on_sale"},
        ]
        for p_data in products_data:
            session.add(Product(**p_data))

        # 创建测试用户
        test_user = User(
            email="test@shop.com",
            nickname="测试用户",
            hashed_password=hash_password("test123"),
            role="user",
            shipping_address="北京市海淀区中关村大街1号",
        )
        session.add(test_user)

        await session.commit()
        print("演示数据初始化完成！")
        print("  管理员: admin@shop.com / admin123")
        print("  测试用户: test@shop.com / test123")


if __name__ == "__main__":
    asyncio.run(seed_data())
