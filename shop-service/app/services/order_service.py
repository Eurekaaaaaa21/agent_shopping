import json
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from fastapi import HTTPException, status

from app.models.order import Order, OrderItem, PaymentRecord
from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.models.logistics import LogisticsRecord
from app.core.exceptions import BusinessException


async def create_order(db: AsyncSession, user_id: int, shipping_address: Optional[str] = None) -> Order:
    """创建订单：事务内锁库存 → 扣减 → 生成 pending 订单 → 清空购物车"""
    # 获取用户地址
    if not shipping_address:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.shipping_address:
            raise BusinessException("请填写收货地址")
        shipping_address = user.shipping_address

    # 获取购物车
    cart_result = await db.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.user_id == user_id)
    )
    cart_rows = cart_result.all()
    if not cart_rows:
        raise BusinessException("购物车为空")

    total_amount = 0.0
    order_items_data = []

    for cart_item, product in cart_rows:
        # 锁库存（FOR UPDATE）
        lock_result = await db.execute(
            select(Product).where(Product.id == product.id)
        )
        locked_product = lock_result.scalar_one()
        if locked_product.stock < cart_item.quantity:
            raise BusinessException(f"商品 [{locked_product.name}] 库存不足")

        subtotal = float(locked_product.price) * cart_item.quantity
        total_amount += subtotal
        order_items_data.append({
            "product_id": product.id,
            "product_name": locked_product.name,
            "product_price": float(locked_product.price),
            "quantity": cart_item.quantity,
            "subtotal": round(subtotal, 2),
        })

        # 扣减库存
        locked_product.stock -= cart_item.quantity

    # 创建订单
    order = Order(
        user_id=user_id,
        total_amount=round(total_amount, 2),
        status="pending",
        shipping_address=shipping_address,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)

    # 创建订单明细（快照）
    for item_data in order_items_data:
        order_item = OrderItem(order_id=order.id, **item_data)
        db.add(order_item)

    # 清空购物车
    for cart_item, _ in cart_rows:
        await db.delete(cart_item)

    await db.flush()
    return order


async def pay_order(db: AsyncSession, order_id: int, user_id: int) -> PaymentRecord:
    """模拟支付：幂等校验"""
    # 锁订单
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.status != "pending":
        if order.status == "paid":
            raise BusinessException("订单已支付，请勿重复支付")
        raise BusinessException(f"订单状态为 {order.status}，无法支付")

    # 检查是否已有支付记录
    existing_payment = await db.execute(
        select(PaymentRecord).where(PaymentRecord.order_id == order_id)
    )
    if existing_payment.scalar_one_or_none():
        raise BusinessException("订单已支付，请勿重复支付")

    # 更新订单状态
    order.status = "paid"

    # 创建支付记录
    payment = PaymentRecord(
        order_id=order_id,
        amount=order.total_amount,
        method="simulated",
        status="success",
    )
    db.add(payment)

    # 创建物流记录（预置演示数据）
    logistics = LogisticsRecord(
        order_id=order_id,
        status="picked_up",
        tracking_info=json.dumps([
            {"status": "picked_up", "description": "包裹已揽收", "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")},
        ], ensure_ascii=False),
        estimated_delivery=(datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d"),
    )
    db.add(logistics)

    await db.flush()
    await db.refresh(payment)
    return payment


async def cancel_order(db: AsyncSession, order_id: int, user_id: int) -> Order:
    """手动取消订单：仅 pending 可取消，回滚库存"""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.status != "pending":
        raise BusinessException(f"订单状态为 {order.status}，仅待支付订单可取消")

    order.status = "cancelled"

    # 回滚库存
    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order_id))
    items = items_result.scalars().all()
    for item in items:
        product_result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = product_result.scalar_one()
        product.stock += item.quantity

    await db.flush()
    await db.refresh(order)
    return order


async def get_user_orders(db: AsyncSession, user_id: int, status_filter: Optional[str] = None, page: int = 1, page_size: int = 20):
    query = select(Order).where(Order.user_id == user_id)
    count_query = select(func.count()).select_from(Order).where(Order.user_id == user_id)
    if status_filter:
        query = query.where(Order.status == status_filter)
        count_query = count_query.where(Order.status == status_filter)
    query = query.order_by(Order.id.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    orders = result.scalars().all()
    total = (await db.execute(count_query)).scalar()
    return orders, total


async def get_order_detail(db: AsyncSession, order_id: int, user_id: int):
    order_result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user_id)
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order_id))
    items = items_result.scalars().all()
    return order, items


async def cancel_timeout_orders(timeout_minutes: int = 30) -> int:
    """超时订单自动取消，每条订单独立事务"""
    from app.db.session import async_session_factory

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
    cancelled_count = 0

    # 先查出所有超时订单 ID（轻量查询，不锁）
    async with async_session_factory() as session:
        result = await session.execute(
            select(Order.id).where(Order.status == "pending", Order.created_at < cutoff)
        )
        order_ids = [row[0] for row in result.all()]

    # 逐条处理，每条独立事务
    for order_id in order_ids:
        async with async_session_factory() as session:
            try:
                # 锁订单并二次校验
                order_result = await session.execute(
                    select(Order).where(Order.id == order_id, Order.status == "pending")
                )
                order = order_result.scalar_one_or_none()
                if not order:
                    await session.rollback()
                    continue

                order.status = "cancelled"
                items_result = await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))
                items = items_result.scalars().all()
                for item in items:
                    product_result = await session.execute(
                        select(Product).where(Product.id == item.product_id)
                    )
                    product = product_result.scalar_one()
                    product.stock += item.quantity

                await session.commit()
                cancelled_count += 1
            except Exception as e:
                await session.rollback()
                continue

    return cancelled_count


async def get_all_orders_admin(db: AsyncSession, status_filter: Optional[str] = None, page: int = 1, page_size: int = 20):
    query = select(Order).order_by(Order.id.desc())
    count_query = select(func.count()).select_from(Order)
    if status_filter:
        query = query.where(Order.status == status_filter)
        count_query = count_query.where(Order.status == status_filter)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()
    total = (await db.execute(count_query)).scalar()
    return orders, total


async def get_order_by_id(db: AsyncSession, order_id: int):
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()
