from fastapi import APIRouter, Response, status

from app.dependencies import AdminDep, CategoryServiceDep
from app.schemas import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


def response(item, post_count: int = 0) -> CategoryResponse:
    return CategoryResponse.model_validate(item).model_copy(update={"post_count": post_count})


@router.get("", response_model=list[CategoryResponse])
async def list_categories(service: CategoryServiceDep): return [response(item, count) for item, count in await service.list()]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, service: CategoryServiceDep): return response(await service.get(category_id))


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, service: CategoryServiceDep, _admin: AdminDep): return response(await service.create(data))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, service: CategoryServiceDep, _admin: AdminDep): await service.delete(category_id); return Response(status_code=204)
