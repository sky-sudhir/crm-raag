from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from typing import List

from api.models.reserved_subdomain import ReservedSubdomain
from api.schemas.reserved_subdomain import ReservedSubdomainCreate, ReservedSubdomainUpdate

class ReservedSubdomainService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_subdomain(self, data: ReservedSubdomainCreate) -> ReservedSubdomain:
        stmt = select(ReservedSubdomain).where(ReservedSubdomain.subdomain == data.subdomain.lower())
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subdomain '{data.subdomain}' is already reserved."
            )
        
        new_subdomain = ReservedSubdomain(
            subdomain=data.subdomain.lower(),
            description=data.description
        )
        self.session.add(new_subdomain)
        await self.session.commit()
        await self.session.refresh(new_subdomain)
        return new_subdomain

    async def get_all_subdomains(self) -> List[ReservedSubdomain]:
        stmt = select(ReservedSubdomain).order_by(ReservedSubdomain.subdomain)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_subdomain_by_id(self, subdomain_id: str) -> ReservedSubdomain:
        subdomain = await self.session.get(ReservedSubdomain, subdomain_id)
        if not subdomain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reserved subdomain with ID '{subdomain_id}' not found."
            )
        return subdomain

    async def update_subdomain(self, subdomain_id: str, data: ReservedSubdomainUpdate) -> ReservedSubdomain:
        subdomain_to_update = await self.get_subdomain_by_id(subdomain_id)
        
        update_data = data.model_dump(exclude_unset=True)

        if 'subdomain' in update_data and update_data['subdomain'].lower() != subdomain_to_update.subdomain:
            new_subdomain_name = update_data['subdomain'].lower()
            stmt = select(ReservedSubdomain).where(ReservedSubdomain.subdomain == new_subdomain_name)
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Subdomain '{new_subdomain_name}' is already reserved."
                )
            subdomain_to_update.subdomain = new_subdomain_name

        if 'description' in update_data:
            subdomain_to_update.description = update_data['description']

        await self.session.commit()
        await self.session.refresh(subdomain_to_update)
        return subdomain_to_update

    async def delete_subdomain(self, subdomain_id: str) -> None:
        subdomain_to_delete = await self.get_subdomain_by_id(subdomain_id)
        await self.session.delete(subdomain_to_delete)
        await self.session.commit()