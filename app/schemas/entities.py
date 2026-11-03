from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Role(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    USER = "user"


class PostStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class InputModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class UserCreate(InputModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-z0-9_]+$")
    email: EmailStr
    role: Role = Role.USER
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(InputModel):
    email: EmailStr | None = None
    role: Role | None = None
    is_active: bool | None = None

    @field_validator("email", "role", "is_active")
    @classmethod
    def not_null(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("no puede ser null")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime


class RegisterRequest(InputModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(InputModel):
    refresh_token: str


class CategoryCreate(InputModel):
    name: str = Field(min_length=2, max_length=80)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str | None
    created_at: datetime
    post_count: int = 0


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str


class PostCreate(InputModel):
    title: str = Field(min_length=3, max_length=200)
    slug: str = Field(min_length=3, max_length=200, pattern=r"^[a-z0-9-]+$")
    content: str = Field(min_length=10)
    excerpt: str | None = Field(default=None, max_length=500)
    status: PostStatus = PostStatus.DRAFT
    category_id: int | None = Field(default=None, gt=0)
    tags: list[str] = Field(default_factory=list, max_length=10)


class PostUpdate(InputModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    slug: str | None = Field(default=None, min_length=3, max_length=200, pattern=r"^[a-z0-9-]+$")
    content: str | None = Field(default=None, min_length=10)
    excerpt: str | None = Field(default=None, max_length=500)
    status: PostStatus | None = None
    category_id: int | None = Field(default=None, gt=0)
    tags: list[str] | None = Field(default=None, max_length=10)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    slug: str
    content: str
    excerpt: str | None
    status: PostStatus
    published_at: datetime | None
    author: UserResponse
    category: CategoryResponse | None
    tags: list[TagResponse]
    created_at: datetime
    updated_at: datetime


class PostPage(BaseModel):
    items: list[PostResponse]
    total: int
    skip: int
    limit: int


class CommentCreate(InputModel):
    content: str = Field(min_length=2, max_length=2000)


class CommentUpdate(InputModel):
    content: str = Field(min_length=2, max_length=2000)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    author: UserResponse
    created_at: datetime
    updated_at: datetime

