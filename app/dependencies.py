from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth_service import AuthService
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models import User
from app.schemas import PostStatus
from app.services import CategoryService, CommentService, PostService, UserService


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService: return UserService(db)
def get_category_service(db: AsyncSession = Depends(get_db)) -> CategoryService: return CategoryService(db)
def get_post_service(db: AsyncSession = Depends(get_db)) -> PostService: return PostService(db)
def get_comment_service(db: AsyncSession = Depends(get_db)) -> CommentService: return CommentService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
PostServiceDep = Annotated[PostService, Depends(get_post_service)]
CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService: return AuthService(db)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    from app.security import decode_token
    payload = decode_token(token, "access")
    user = await db.get(User, int(payload["sub"]))
    if not user or not user.is_active: raise UnauthorizedError("El usuario no está activo")
    return user


async def get_optional_user(token: str | None = Depends(optional_oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User | None:
    if token is None: return None
    return await get_current_user(token, db)


def require_roles(*roles: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles: raise ForbiddenError("No tengo permisos para esta operación")
        return user
    return checker


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]
AdminDep = Annotated[User, Depends(require_roles("admin"))]
EditorDep = Annotated[User, Depends(require_roles("admin", "editor"))]


class PaginationParams:
    def __init__(self, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)) -> None: self.skip = skip; self.limit = limit


class PostFilterParams:
    def __init__(self, status: PostStatus | None = None, category_id: int | None = Query(None, gt=0), tag: str | None = None, author_id: int | None = Query(None, gt=0)) -> None:
        self.status = status; self.category_id = category_id; self.tag = tag; self.author_id = author_id

