from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, Comment, Post, Tag, User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None: self.db = db
    async def list(self, skip: int, limit: int) -> list[User]:
        return list((await self.db.scalars(select(User).order_by(User.id).offset(skip).limit(limit))).all())
    async def get(self, user_id: int) -> User | None: return await self.db.get(User, user_id)
    async def add(self, item: User) -> User: self.db.add(item); await self.db.flush(); await self.db.refresh(item); return item
    async def count_posts(self, user_id: int) -> int: return int(await self.db.scalar(select(func.count(Post.id)).where(Post.author_id == user_id)) or 0)
    async def delete(self, item: User) -> None: await self.db.delete(item); await self.db.flush()


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None: self.db = db
    async def list(self) -> list[tuple[Category, int]]:
        rows = await self.db.execute(select(Category, func.count(Post.id)).outerjoin(Post).group_by(Category.id).order_by(Category.id))
        return [(row[0], int(row[1])) for row in rows.all()]
    async def get(self, category_id: int) -> Category | None: return await self.db.get(Category, category_id)
    async def add(self, item: Category) -> Category: self.db.add(item); await self.db.flush(); await self.db.refresh(item); return item
    async def delete(self, item: Category) -> None: await self.db.delete(item); await self.db.flush()


class TagRepository:
    def __init__(self, db: AsyncSession) -> None: self.db = db
    async def by_slugs(self, slugs: list[str]) -> list[Tag]:
        if not slugs: return []
        return list((await self.db.scalars(select(Tag).where(Tag.slug.in_(slugs)).order_by(Tag.id))).all())


class PostRepository:
    OPTIONS = (selectinload(Post.author), selectinload(Post.category), selectinload(Post.tags))
    def __init__(self, db: AsyncSession) -> None: self.db = db
    async def get(self, post_id: int) -> Post | None:
        return await self.db.scalar(select(Post).where(Post.id == post_id).options(*self.OPTIONS))
    async def page(self, skip: int, limit: int, status: str | None, category_id: int | None, tag: str | None, author_id: int | None) -> tuple[list[Post], int]:
        filters = []
        if status: filters.append(Post.status == status)
        if category_id: filters.append(Post.category_id == category_id)
        if author_id: filters.append(Post.author_id == author_id)
        query = select(Post).where(*filters)
        count_query = select(func.count(Post.id)).where(*filters)
        if tag:
            query = query.join(Post.tags).where(Tag.slug == tag)
            count_query = count_query.join(Post.tags).where(Tag.slug == tag)
        total = int(await self.db.scalar(count_query) or 0)
        items = list((await self.db.scalars(query.options(*self.OPTIONS).order_by(Post.id).offset(skip).limit(limit))).unique().all())
        return items, total
    async def add(self, item: Post) -> Post: self.db.add(item); await self.db.flush(); return item
    async def delete(self, item: Post) -> None: await self.db.delete(item); await self.db.flush()


class CommentRepository:
    OPTIONS = (selectinload(Comment.author),)
    def __init__(self, db: AsyncSession) -> None: self.db = db
    async def get(self, comment_id: int) -> Comment | None: return await self.db.scalar(select(Comment).where(Comment.id == comment_id).options(*self.OPTIONS))
    async def list_for_post(self, post_id: int) -> list[Comment]: return list((await self.db.scalars(select(Comment).where(Comment.post_id == post_id).options(*self.OPTIONS).order_by(Comment.created_at))).all())
    async def add(self, item: Comment) -> Comment: self.db.add(item); await self.db.flush(); return item
    async def delete(self, item: Comment) -> None: await self.db.delete(item); await self.db.flush()

