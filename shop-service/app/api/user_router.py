from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user_id, require_admin
from app.core.exceptions import BusinessException
from app.schemas.user import UserRegister, UserLogin, UserUpdate, PasswordChange, UserOut, TokenOut
from app.schemas.common import ResponseBase
from app.services import user_service
from app.core.security import verify_password, create_access_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["用户"])


@router.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await user_service.create_user(db, data.email, data.nickname, data.password)
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
async def update_profile(data: UserUpdate, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await user_service.update_user_info(db, user_id, data.nickname)
    if data.shipping_address is not None:
        user = await user_service.update_user_address(db, user_id, data.shipping_address)
    return UserOut.model_validate(user)


@router.put("/me/password")
async def change_password(data: PasswordChange, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await user_service.change_password(db, user_id, data.old_password, data.new_password)
    return ResponseBase(message="密码修改成功")


@router.get("/list", response_model=dict)
async def list_users(auth: dict = Depends(require_admin), db: AsyncSession = Depends(get_db), page: int = 1, page_size: int = 20):
    users, total = await user_service.get_user_list(db, page, page_size)
    return {
        "items": [UserOut.model_validate(u).model_dump() for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
