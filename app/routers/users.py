from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import AdminDep, UserServiceDep
from app.schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def list_users(service: UserServiceDep, _admin: AdminDep, skip: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return await service.list(skip, limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: UserServiceDep, _admin: AdminDep): return await service.get(user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, service: UserServiceDep, _admin: AdminDep): return await service.create(data)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate, service: UserServiceDep, _admin: AdminDep): return await service.update(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, service: UserServiceDep, _admin: AdminDep): await service.delete(user_id); return Response(status_code=204)
