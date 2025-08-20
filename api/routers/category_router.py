


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.db.tenant import get_db_tenant
from api.middleware.jwt_middleware import get_current_user
from api.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead
from api.services.category_service import CategoryService
from api.utils.util_response import APIResponse

router = APIRouter(
    prefix="/api/categories",
    tags=["Category"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", response_model=CategoryRead, status_code=201, summary="Create a new category")
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db_tenant)
):
    """Create a new category."""
    category_service = CategoryService(db)
    return await category_service.create_category(category_data)

@router.get("/", response_model=List[CategoryRead], summary="Get all categories")
async def get_categories(db: AsyncSession = Depends(get_db_tenant)):
    """Get all categories."""
    category_service = CategoryService(db)
    return await category_service.get_all_categories()

@router.get("/{category_id}", response_model=CategoryRead, summary="Get category by ID")
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db_tenant)
):
    """Get a specific category by ID."""
    category_service = CategoryService(db)
    return await category_service.get_category_by_id(category_id)

@router.put("/{category_id}", response_model=CategoryRead, summary="Update category")
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db_tenant)
):
    """Update a category."""
    category_service = CategoryService(db)
    return await category_service.update_category(category_id, category_data)

@router.delete("/{category_id}", summary="Delete category")
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db_tenant)
):
    """Delete a category."""
    category_service = CategoryService(db)
    await category_service.delete_category(category_id)
    return {"message": "Category deleted successfully"}


