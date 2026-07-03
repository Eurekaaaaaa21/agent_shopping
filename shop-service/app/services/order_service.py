import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BusinessException
from app.models.cart import CartItem
from app.models.logistics import LogisticsRecord
from app.models.order import Order, OrderItem, PaymentRecord, utc_now_naive
from app.models.product import Product
from app.models.user import User

logger = logging.getLogger(__name__)


async def create_order(db: AsyncSession, user_id: int, shipping_address: Optional[str] = None) -> Order:
    """创建订单：事务内锁库存、扣减库存、生成订单和明细、清空购物车。"""
    if not shipping_address:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.shipping_address:
            raise BusinessException("请填写收货地址")
        shipping_address = user.shipping_address

    cart_result = await db.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.user_id == user_id)
    )
    cart_rows = cart_result.all()
    if not cart_rows:
        raise BusinessException("购物车为空")

    total_amount = Decimal("0.00")
    order_items_data = []

    for cart_item, product in cart_rows:
        lock_result = await db.execute(
            select(Product).where(Product.id == product.id).with_for_update()
        )
        locked_product = lock_result.scalar_one()
        if locked_product.stock < cart_item.quantity:
            raise BusinessException(f"商品 [{locked_product.name}] 库存不足")

        price = Decimal(str(locked_product.price))
        subtotal = price * cart_item.quantity
        total_amount += subtotal
        order_items_data.append(
            {
                "product_id": product.id,
                "product_name": locked_product.name,
                "product_price": price,
                "quantity": cart_item.quantity,
                "subtotal": subtotal,
            }
        )

        locked_product.stock -= cart_item.quantity

    order = Order(
        user_id=user_id,
        total_amount=total_amount,
        status="pending",
        shipping_address=shipping_address,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)

    for item_data in order_items_data:
        db.add(OrderItem(order_id=order.id, **item_data))

    for cart_item, _ in cart_rows:
        await db.delete(cart_item)

    await db.flush()
    return order


async def pay_order(db: AsyncSession, order_id: int, user_id: int) -> PaymentRecord:
    """模拟支付：pending 订单支付成功后生成支付记录和物流记录。"""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user_id).with_for_update()
    )
    order = result.scalar_one_or_none()
    if not order:
        raise BusinessException(detail="订单不存在", status_code=status.HTTP_404_NOT_FOUND)
    if order.status != "pending":
        if order.status == "paid":
            raise BusinessException("订单已支付，请勿重复支付")
        raise BusinessException(f"订单状态为 {order.status}，无法支付")

    existing_payment = await db.execute(
        select(PaymentRecord).where(PaymentRecord.order_id == order_id)
    )
    if existing_payment.scalar_one_or_none():
        raise BusinessException("订单已支付，请勿重复支付")

    order.status = "paid"
    order.paid_at = utc_now_naive()

    payment = PaymentRecord(
        order_id=order_id,
        amount=order.total_amount,
        method="simulated",
        status="success",
    )
    db.add(payment)

    logistics = LogisticsRecord(
        order_id=order_id,
        status="picked_up",
        tracking_info=json.dumps(
            [
                {
                    "status": "picked_up",
                    "description": "包裹已揽收",
                    "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                }
            ],
            ensure_ascii=False,
        ),
        estimated_delivery=(datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d"),
    )
    db.add(logistics)

    await db.flush()
    await db.refresh(payment)
    return payment


async def cancel_order(db: AsyncSession, order_id: int, user_id: int) -> Order:
    """手动取消订单：仅 pending 订单可取消，并回滚库存。"""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user_id).with_for_update()
    )
    order = result.scalar_one_or_none()
    if not order:
        raise BusinessException(detail="订单不存在", status_code=status.HTTP_404_NOT_FOUND)
    if order.status != "pending":
        raise BusinessException(f"订单状态为 {order.status}，仅待支付订单可取消")

    order.status = "cancelled"
    order.cancelled_at = utc_now_naive()

    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order_id))
    items = items_result.scalars().all()
    for item in items:
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id).with_for_update()
        )
        product = product_result.scalar_one()
        product.stock += item.quantity

    await db.flush()
    await db.refresh(order)
    return order


async def get_user_orders(
    db: AsyncSession,
    user_id: int,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user_id)
    )
    count_query = select(func.count()).select_from(Order).where(Order.user_id == user_id)
    if status_filter:
        query = query.where(Order.status == status_filter)
        count_query = count_query.where(Order.status == status_filter)
    query = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    orders = result.scalars().all()
    total = (await db.execute(count_query)).scalar()
    return orders, total


async def get_order_detail(db: AsyncSession, order_id: int, user_id: int):
    order_result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise BusinessException(detail="订单不存在", status_code=status.HTTP_404_NOT_FOUND)

    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order_id))
    items = items_result.scalars().all()
    return order, items


async def cancel_timeout_orders(timeout_minutes: int = 30) -> int:
    """超时订单自动取消，每条订单独立事务。"""
    from app.db.session import async_session_factory

    cutoff = utc_now_naive() - timedelta(minutes=timeout_minutes)
    cancelled_count = 0

    async with async_session_factory() as session:
        result = await session.execute(
            select(Order.id).where(Order.status == "pending", Order.created_at < cutoff)
        )
        order_ids = [row[0] for row in result.all()]

    for order_id in order_ids:
        async with async_session_factory() as session:
            try:
                order_result = await session.execute(
                    select(Order)
                    .where(Order.id == order_id, Order.status == "pending")
                    .with_for_update()
                )
                order = order_result.scalar_one_or_none()
                if not order:
                    await session.rollback()
                    continue

                order.status = "cancelled"
                order.cancelled_at = utc_now_naive()

                items_result = await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))
                items = items_result.scalars().all()
                for item in items:
                    product_result = await session.execute(
                        select(Product).where(Product.id == item.product_id).with_for_update()
                    )
                    product = product_result.scalar_one()
                    product.stock += item.quantity

                await session.commit()
                cancelled_count += 1
                logger.info("超时取消订单成功: order_id=%s", order_id)
            except Exception:
                logger.exception("超时取消订单失败: order_id=%s", order_id)
                await session.rollback()
                continue

    return cancelled_count


async def get_all_orders_admin(
    db: AsyncSession,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
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
