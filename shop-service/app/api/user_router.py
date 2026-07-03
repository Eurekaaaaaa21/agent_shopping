import logging
import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, require_admin
from app.core.exceptions import BusinessException
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.schemas.common import ResponseBase
from app.schemas.user import PasswordChange, TokenOut, UserLogin, UserOut, UserRegister, UserUpdate
from app.services import user_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["用户"])

ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024
AVATAR_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "avatars")


@router.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await user_service.create_user(db, data.email, data.nickname, data.password, data.phone)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return ResponseBase(
        data=TokenOut(
            access_token=token,
            user=UserOut.model_validate(user),
        ).model_dump()
    )


@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise BusinessException("邮箱或密码错误")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return ResponseBase(
        data=TokenOut(
            access_token=token,
            user=UserOut.model_validate(user),
        ).model_dump()
    )


@router.get("/me", response_model=UserOut)
async def get_profile(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise BusinessException("用户不存在")
    return UserOut.model_validate(user)


@router.put("/me", response_model=UserOut)
async def update_profile(
    data: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.update_user_info(db, user_id, data.nickname, data.phone, data.avatar)
    if data.shipping_address is not None:
        user = await user_service.update_user_address(db, user_id, data.shipping_address)
    return UserOut.model_validate(user)


@router.put("/me/password")
async def change_password(
    data: PasswordChange,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await user_service.change_password(db, user_id, data.old_password, data.new_password)
    return ResponseBase(message="密码修改成功")


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise BusinessException("仅支持 JPG/PNG/GIF/WebP 格式的图片")

    contents = await file.read()
    if len(contents) > MAX_AVATAR_SIZE:
        raise BusinessException("图片大小不能超过 2MB")
    await file.seek(0)

    ext = os.path.splitext(file.filename or ".png")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        ext = ".png"
    filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"

    os.makedirs(AVATAR_DIR, exist_ok=True)

    filepath = os.path.join(AVATAR_DIR, filename)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(contents)

    avatar_url = f"/static/avatars/{filename}"
    old_user = await user_service.get_user_by_id(db, user_id)
    old_avatar = old_user.avatar if old_user else None
    user = await user_service.update_user_info(db, user_id, avatar=avatar_url)

    if old_avatar and old_avatar != avatar_url:
        old_path = os.path.join(AVATAR_DIR, os.path.basename(old_avatar))
        if os.path.exists(old_path) and old_path != filepath:
            os.remove(old_path)

    return ResponseBase(data={"avatar_url": avatar_url}, message="头像上传成功")


@router.get("/list")
async def list_users(
    auth: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
):
    users, total = await user_service.get_user_list(db, page, page_size)
    return ResponseBase(
        data={
            "items": [UserOut.model_validate(u).model_dump() for u in users],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )
