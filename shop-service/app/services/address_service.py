from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


async def create_address(db: AsyncSession, user_id: int, data: AddressCreate) -> Address:
    # 如果设为默认，先取消其他默认地址
    if data.is_default:
        await _unset_default(db, user_id)

    address = Address(
        user_id=user_id,
        receiver_name=data.receiver_name,
        phone=data.phone,
        province=data.province,
        city=data.city,
        district=data.district,
        detail=data.detail,
        is_default=data.is_default,
    )
    db.add(address)
    await db.flush()
    await db.refresh(address)
    return address


async def get_addresses(db: AsyncSession, user_id: int) -> List[Address]:
    result = await db.execute(
        select(Address)
        .where(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.created_at.desc())
    )
    return list(result.scalars().all())


async def get_address_by_id(db: AsyncSession, address_id: int, user_id: int) -> Address:
    result = await db.execute(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地址不存在")
    return address


async def update_address(db: AsyncSession, address_id: int, user_id: int, data: AddressUpdate) -> Address:
    address = await get_address_by_id(db, address_id, user_id)

    # 如果设为默认，先取消其他默认地址
    if data.is_default:
        await _unset_default(db, user_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(address, key, value)

    await db.flush()
    await db.refresh(address)
    return address


async def delete_address(db: AsyncSession, address_id: int, user_id: int) -> None:
    address = await get_address_by_id(db, address_id, user_id)
    was_default = address.is_default
    await db.delete(address)
    await db.flush()

    # 如果删除的是默认地址，自动将最新的一条设为默认
    if was_default:
        result = await db.execute(
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.created_at.desc())
            .limit(1)
        )
        next_addr = result.scalar_one_or_none()
        if next_addr:
            next_addr.is_default = True
            await db.flush()


async def set_default_address(db: AsyncSession, address_id: int, user_id: int) -> Address:
    address = await get_address_by_id(db, address_id, user_id)
    await _unset_default(db, user_id)
    address.is_default = True
    await db.flush()
    await db.refresh(address)
    return address


async def _unset_default(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(Address)
        .where(Address.user_id == user_id, Address.is_default == True)
        .values(is_default=False)
    )
    await db.flush()
