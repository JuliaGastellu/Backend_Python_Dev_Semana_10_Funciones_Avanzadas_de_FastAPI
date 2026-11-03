from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Identity, Index, String, Table, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin','editor','user')", name="users_role_check"),)
    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    role: Mapped[str] = mapped_column(String(20), server_default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    hashed_password: Mapped[str] = mapped_column(String(255))
    posts: Mapped[list["Post"]] = relationship(back_populates="author", passive_deletes=True)
    comments: Mapped[list["Comment"]] = relationship(back_populates="author", passive_deletes=True)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    posts: Mapped[list["Post"]] = relationship(back_populates="category", passive_deletes=True)


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    posts: Mapped[list["Post"]] = relationship(secondary=post_tags, back_populates="tags")


class Post(Base):
    __tablename__ = "posts"
    image_filename: Mapped[str | None] = mapped_column(String(100))
    __table_args__ = (
        CheckConstraint("status IN ('draft','published')", name="posts_status_check"),
        CheckConstraint("(status='published' AND published_at IS NOT NULL) OR (status='draft' AND published_at IS NULL)", name="posts_status_published_at_check"),
        Index("idx_posts_author_id", "author_id"),
        Index("idx_posts_status_published_at", "status", text("published_at DESC")),
        Index("idx_posts_drafts_updated_at", text("updated_at DESC"), postgresql_where=text("status='draft'")),
    )
    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    content: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    published_at: Mapped[datetime | None]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    author: Mapped[User] = relationship(back_populates="posts")
    category: Mapped[Category | None] = relationship(back_populates="posts")
    tags: Mapped[list[Tag]] = relationship(secondary=post_tags, back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", order_by="Comment.created_at", passive_deletes=True)


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (Index("idx_comments_post_id", "post_id"), Index("idx_comments_user_id", "user_id"))
    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    post: Mapped[Post] = relationship(back_populates="comments")
    author: Mapped[User] = relationship(back_populates="comments")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("idx_refresh_tokens_user_id", "user_id"), Index("idx_refresh_tokens_expires_at", "expires_at"))
    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    jti_hash: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    user: Mapped[User] = relationship(back_populates="refresh_tokens")

