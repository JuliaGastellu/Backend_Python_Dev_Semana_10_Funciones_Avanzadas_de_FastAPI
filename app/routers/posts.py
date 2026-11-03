from typing import Annotated

from fastapi import APIRouter, Query, Response, status, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.models import Post
from app.database import async_session_factory
from app.storage import save_image, UPLOADS
import csv
import io

from app.dependencies import EditorDep, OptionalUserDep, PostServiceDep
from app.exceptions import ForbiddenError, NotFoundError
from app.schemas import PostCreate, PostPage, PostResponse, PostStatus, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/export")
async def export_posts(user: OptionalUserDep):
    async def rows():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "slug", "title", "status", "published_at", "author"])
        yield buffer.getvalue()
        async with async_session_factory() as db:
            query = select(Post).options(selectinload(Post.author)).order_by(Post.id).execution_options(yield_per=100)
            if user is None or user.role == "user":
                query = query.where(Post.status == "published")
            elif user.role != "admin":
                query = query.where(or_(Post.status == "published", Post.author_id == user.id))
            async for item in await db.stream_scalars(query):
                buffer.seek(0)
                buffer.truncate(0)
                values = [item.id, item.slug, item.title, item.status, item.published_at, item.author.username]
                writer.writerow(["'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v for v in values])
                yield buffer.getvalue()
    return StreamingResponse(rows(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="posts.csv"'})


@router.post("/{post_id}/image")
async def upload_image(post_id: int, file: UploadFile, service: PostServiceDep, user: EditorDep):
    item = await service.get(post_id)
    if user.role != "admin" and item.author_id != user.id:
        raise ForbiddenError("Solo puedo cambiar la imagen de mis posts")
    filename = await save_image(file)
    previous = item.image_filename
    item.image_filename = filename
    try:
        await service.db.commit()
    except Exception:
        await service.db.rollback()
        (UPLOADS / filename).unlink(missing_ok=True)
        raise
    if previous:
        (UPLOADS / previous).unlink(missing_ok=True)
    return {"image_url": f"/api/v1/posts/{post_id}/image"}


@router.get("/{post_id}/image", response_class=FileResponse)
async def get_image(post_id: int, service: PostServiceDep, user: OptionalUserDep):
    item = await service.get(post_id)
    if item.status != "published" and (user is None or (user.role != "admin" and item.author_id != user.id)):
        raise NotFoundError("El post no existe")
    if not item.image_filename or not (UPLOADS / item.image_filename).is_file():
        raise NotFoundError("La imagen no existe")
    return FileResponse(UPLOADS / item.image_filename)


@router.get("", response_model=PostPage)
async def list_posts(service: PostServiceDep, user: OptionalUserDep, skip: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 20, status_filter: PostStatus | None = None, category_id: int | None = None, tag: str | None = None, author_id: int | None = None):
    if user is None or user.role == "user": status_filter = PostStatus.PUBLISHED
    items, total = await service.page(skip=skip, limit=limit, status=status_filter, category_id=category_id, tag=tag, author_id=author_id)
    return PostPage(items=items, total=total, skip=skip, limit=limit)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, service: PostServiceDep, user: OptionalUserDep):
    item = await service.get(post_id)
    if item.status != "published" and (user is None or (user.role not in {"admin", "editor"} and item.author_id != user.id)): raise NotFoundError(f"El post {post_id} no existe")
    return item


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(data: PostCreate, service: PostServiceDep, user: EditorDep): return await service.create(data, user.id)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, data: PostUpdate, service: PostServiceDep, user: EditorDep):
    item = await service.get(post_id)
    if user.role != "admin" and item.author_id != user.id: raise ForbiddenError("Solo puedo editar mis propios posts")
    return await service.update(post_id, data)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, service: PostServiceDep, user: EditorDep):
    item = await service.get(post_id)
    if user.role != "admin" and item.author_id != user.id: raise ForbiddenError("Solo puedo borrar mis propios posts")
    await service.delete(post_id); return Response(status_code=204)
