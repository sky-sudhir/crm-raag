from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from api.models.category import Category
from api.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead
from api.utils.util_response import APIResponse

class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_category(self, category_data: CategoryCreate) -> CategoryRead:
        """Create a new category."""
        # Check if category with same name already exists
        existing_category = await self.get_category_by_name(category_data.name)
        if existing_category:
            raise HTTPException(status_code=400, detail="Category with this name already exists")
        
        category = Category(name=category_data.name)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return CategoryRead.model_validate(category)

    async def get_category_by_id(self, category_id: str) -> Optional[CategoryRead]:
        """Get a category by ID."""
        result = await self.session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return CategoryRead.model_validate(category)

    async def get_category_by_name(self, name: str) -> Optional[CategoryRead]:
        """Get a category by name."""
        result = await self.session.execute(select(Category).where(Category.name == name))
        category = result.scalar_one_or_none()
        return CategoryRead.model_validate(category) if category else None

    async def get_all_categories(self) -> List[CategoryRead]:
        """Get all categories."""
        result = await self.session.execute(select(Category))
        categories = result.scalars().all()
        return [CategoryRead.model_validate(category) for category in categories]

    async def update_category(self, category_id: str, category_data: CategoryUpdate) -> CategoryRead:
        """Update a category."""
        result = await self.session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Check if new name conflicts with existing category
        if category_data.name and category_data.name != category.name:
            existing_category = await self.get_category_by_name(category_data.name)
            if existing_category:
                raise HTTPException(status_code=400, detail="Category with this name already exists")

        # Update fields if provided
        if category_data.name is not None:
            category.name = category_data.name

        await self.session.commit()
        await self.session.refresh(category)
        return CategoryRead.model_validate(category)

    async def delete_category(self, category_id: str) -> bool:
        """Delete a category."""
        result = await self.session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        await self.session.execute(delete(Category).where(Category.id == category_id))
        await self.session.commit()
        return True
