from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import hash_password, verify_password


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, nickname: str, password: str) -> User:
    existing = await get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已注册")
    user = User(
        email=email,
        nickname=nickname,
        hashed_password=hash_password(password),
        role="user",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_list(db: AsyncSession, page: int = 1, page_size: int = 20):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(User).order_by(User.id.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()
    from sqlalchemy import func
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar()
    return users, total


async def update_user_address(db: AsyncSession, user_id: int, address: str) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.shipping_address = address
    await db.flush()
    await db.refresh(user)
    return user


async def update_user_info(db: AsyncSession, user_id: int, nickname: Optional[str] = None) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if nickname:
        user.nickname = nickname
    await db.flush()
    await db.refresh(user)
    return user


async def change_password(db: AsyncSession, user_id: int, old_password: str, new_password: str) -> None:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误")
    user.hashed_password = hash_password(new_password)
    await db.flush()
