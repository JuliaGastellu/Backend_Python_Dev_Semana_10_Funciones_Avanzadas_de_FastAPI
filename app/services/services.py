from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DuplicateError, InUseError, NotFoundError
from app.models import Category, Comment, Post, User
from app.security import hash_password
from app.repositories import CategoryRepository, CommentRepository, PostRepository, TagRepository, UserRepository
from app.schemas import CategoryCreate, CommentCreate, CommentUpdate, PostCreate, PostUpdate, UserCreate, UserUpdate


async def commit_or_duplicate(db: AsyncSession, detail: str) -> None:
    try: await db.commit()
    except IntegrityError as exc:
        await db.rollback(); raise DuplicateError(detail) from exc


class UserService:
    def __init__(self, db: AsyncSession) -> None: self.db = db; self.repo = UserRepository(db)
    async def list(self, skip: int, limit: int) -> list[User]: return await self.repo.list(skip, limit)
    async def get(self, user_id: int) -> User:
        item = await self.repo.get(user_id)
        if not item: raise NotFoundError(f"El usuario {user_id} no existe")
        return item
    async def create(self, data: UserCreate) -> User:
        payload = data.model_dump(exclude={"password"}); payload["hashed_password"] = hash_password(data.password)
        item = await self.repo.add(User(**payload))
        await commit_or_duplicate(self.db, "El username o email ya existe"); await self.db.refresh(item); return item
    async def update(self, user_id: int, data: UserUpdate) -> User:
        item = await self.get(user_id)
        for key, value in data.model_dump(exclude_unset=True).items(): setattr(item, key, value)
        await commit_or_duplicate(self.db, "El email ya existe"); await self.db.refresh(item); return item
    async def delete(self, user_id: int) -> None:
        item = await self.get(user_id)
        if await self.repo.count_posts(user_id): raise InUseError("No puedo borrar un usuario que tiene posts")
        await self.repo.delete(item); await self.db.commit()


class CategoryService:
    def __init__(self, db: AsyncSession) -> None: self.db = db; self.repo = CategoryRepository(db)
    async def list(self) -> list[tuple[Category, int]]: return await self.repo.list()
    async def get(self, category_id: int) -> Category:
        item = await self.repo.get(category_id)
        if not item: raise NotFoundError(f"La categoría {category_id} no existe")
        return item
    async def create(self, data: CategoryCreate) -> Category:
        item = await self.repo.add(Category(**data.model_dump()))
        await commit_or_duplicate(self.db, "El nombre o slug de la categoría ya existe"); await self.db.refresh(item); return item
    async def delete(self, category_id: int) -> None:
        await self.repo.delete(await self.get(category_id)); await self.db.commit()


class PostService:
    def __init__(self, db: AsyncSession) -> None: self.db = db; self.repo = PostRepository(db); self.users = UserRepository(db); self.categories = CategoryRepository(db); self.tags = TagRepository(db)
    async def get(self, post_id: int) -> Post:
        item = await self.repo.get(post_id)
        if not item: raise NotFoundError(f"El post {post_id} no existe")
        return item
    async def page(self, **kwargs: object) -> tuple[list[Post], int]: return await self.repo.page(**kwargs)  # type: ignore[arg-type]
    async def _references(self, author_id: int, category_id: int | None, tag_slugs: list[str]) -> tuple[User, Category | None, list]:
        author = await self.users.get(author_id)
        if not author: raise NotFoundError(f"El usuario {author_id} no existe")
        category = await self.categories.get(category_id) if category_id else None
        if category_id and not category: raise NotFoundError(f"La categoría {category_id} no existe")
        tags = await self.tags.by_slugs(tag_slugs)
        missing = set(tag_slugs) - {tag.slug for tag in tags}
        if missing: raise NotFoundError(f"El tag {sorted(missing)[0]} no existe")
        return author, category, tags
    async def create(self, data: PostCreate, author_id: int) -> Post:
        author, category, tags = await self._references(author_id, data.category_id, data.tags)
        payload = data.model_dump(exclude={"tags", "category_id"})
        payload["published_at"] = datetime.now(timezone.utc) if data.status == "published" else None
        item = Post(**payload, author=author, category=category, tags=tags)
        await self.repo.add(item); await commit_or_duplicate(self.db, "El slug del post ya existe")
        return await self.get(item.id)
    async def update(self, post_id: int, data: PostUpdate) -> Post:
        item = await self.get(post_id); changes = data.model_dump(exclude_unset=True)
        if "category_id" in changes:
            category_id = changes.pop("category_id"); item.category = await self.categories.get(category_id) if category_id else None
            if category_id and item.category is None: raise NotFoundError(f"La categoría {category_id} no existe")
        if "tags" in changes:
            slugs = changes.pop("tags"); tags = await self.tags.by_slugs(slugs)
            if len(tags) != len(set(slugs)): raise NotFoundError("Uno de los tags no existe")
            item.tags = tags
        for key, value in changes.items(): setattr(item, key, value)
        if "status" in changes: item.published_at = datetime.now(timezone.utc) if item.status == "published" else None
        await commit_or_duplicate(self.db, "El slug del post ya existe")
        return await self.get(item.id)
    async def delete(self, post_id: int) -> None: await self.repo.delete(await self.get(post_id)); await self.db.commit()


class CommentService:
    def __init__(self, db: AsyncSession) -> None: self.db = db; self.repo = CommentRepository(db); self.posts = PostRepository(db); self.users = UserRepository(db)
    async def get(self, comment_id: int) -> Comment:
        item = await self.repo.get(comment_id)
        if not item: raise NotFoundError(f"El comentario {comment_id} no existe")
        return item
    async def list(self, post_id: int) -> list[Comment]:
        if not await self.posts.get(post_id): raise NotFoundError(f"El post {post_id} no existe")
        return await self.repo.list_for_post(post_id)
    async def create(self, post_id: int, data: CommentCreate, user_id: int) -> Comment:
        post = await self.posts.get(post_id); user = await self.users.get(user_id)
        if not post: raise NotFoundError(f"El post {post_id} no existe")
        if not user: raise NotFoundError(f"El usuario {user_id} no existe")
        item = await self.repo.add(Comment(content=data.content, post_id=post_id, user_id=user_id)); await self.db.commit(); return await self.get(item.id)
    async def update(self, comment_id: int, data: CommentUpdate) -> Comment:
        item = await self.get(comment_id); item.content = data.content; await self.db.commit(); await self.db.refresh(item); return await self.get(item.id)
    async def delete(self, comment_id: int) -> None: await self.repo.delete(await self.get(comment_id)); await self.db.commit()

