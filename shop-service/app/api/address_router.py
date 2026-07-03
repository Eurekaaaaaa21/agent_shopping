from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user_id
from app.schemas.address import AddressCreate, AddressUpdate, AddressOut
from app.schemas.common import ResponseBase
from app.services import address_service

router = APIRouter(prefix="/users/me/addresses", tags=["收货地址"])


@router.post("")
async def create_address(
    data: AddressCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    address = await address_service.create_address(db, user_id, data)
    return ResponseBase(data=AddressOut.model_validate(address).model_dump(), message="地址添加成功")


@router.get("")
async def list_addresses(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    addresses = await address_service.get_addresses(db, user_id)
    return ResponseBase(
        data=[AddressOut.model_validate(a).model_dump() for a in addresses]
    )


@router.get("/{address_id}")
async def get_address(
    address_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    address = await address_service.get_address_by_id(db, address_id, user_id)
    return ResponseBase(data=AddressOut.model_validate(address).model_dump())


@router.put("/{address_id}")
async def update_address(
    address_id: int,
    data: AddressUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    address = await address_service.update_address(db, address_id, user_id, data)
    return ResponseBase(data=AddressOut.model_validate(address).model_dump(), message="地址更新成功")


@router.delete("/{address_id}")
async def delete_address(
    address_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await address_service.delete_address(db, address_id, user_id)
    return ResponseBase(message="地址已删除")


@router.put("/{address_id}/default")
async def set_default_address(
    address_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    address = await address_service.set_default_address(db, address_id, user_id)
    return ResponseBase(data=AddressOut.model_validate(address).model_dump(), message="已设为默认地址")
