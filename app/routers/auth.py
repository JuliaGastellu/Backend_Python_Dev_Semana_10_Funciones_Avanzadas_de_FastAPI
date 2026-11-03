from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from app.tasks import analytics
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from app.dependencies import AuthServiceDep, CurrentUserDep
from app.schemas import RefreshRequest, RegisterRequest, TokenPair, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, service: AuthServiceDep, background_tasks: BackgroundTasks):
    user = await service.register(data)
    background_tasks.add_task(analytics, user.id)
    return user


@router.post("/token", response_model=TokenPair)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], service: AuthServiceDep):
    return await service.issue_pair(await service.authenticate(form.username, form.password))


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshRequest, service: AuthServiceDep): return await service.rotate(data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, service: AuthServiceDep): await service.logout(data.refresh_token); return Response(status_code=204)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUserDep): return user
