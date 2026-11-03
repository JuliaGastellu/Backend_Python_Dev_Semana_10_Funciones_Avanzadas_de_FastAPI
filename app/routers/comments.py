from fastapi import APIRouter, BackgroundTasks, Response, status
from app.tasks import notify_comment

from app.dependencies import CommentServiceDep, CurrentUserDep
from app.exceptions import ForbiddenError
from app.schemas import CommentCreate, CommentResponse, CommentUpdate

router = APIRouter(tags=["comments"])


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
async def list_comments(post_id: int, service: CommentServiceDep): return await service.list(post_id)


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(post_id: int, data: CommentCreate, service: CommentServiceDep, user: CurrentUserDep, background_tasks: BackgroundTasks):
    post = await service.posts.get(post_id)
    if post is None or post.status != "published":
        from app.exceptions import NotFoundError
        raise NotFoundError("El post no existe")
    item = await service.create(post_id, data, user.id)
    background_tasks.add_task(notify_comment, post_id, post.author_id, user.id)
    return item


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(comment_id: int, data: CommentUpdate, service: CommentServiceDep, user: CurrentUserDep):
    item = await service.get(comment_id)
    if user.role != "admin" and item.user_id != user.id: raise ForbiddenError("Solo puedo editar mis propios comentarios")
    return await service.update(comment_id, data)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int, service: CommentServiceDep, user: CurrentUserDep):
    item = await service.get(comment_id)
    if user.role != "admin" and item.user_id != user.id: raise ForbiddenError("Solo puedo borrar mis propios comentarios")
    await service.delete(comment_id); return Response(status_code=204)
