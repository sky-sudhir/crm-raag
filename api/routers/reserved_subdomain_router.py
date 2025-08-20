from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.db.tenant import get_db_public
from api.services.reserved_subdomain_service import ReservedSubdomainService
from api.schemas.reserved_subdomain import ReservedSubdomainRead, ReservedSubdomainCreate, ReservedSubdomainUpdate
from api.middleware.jwt_middleware import get_current_user 
from api.models.user import UserRole

# This is a placeholder for a proper admin check dependency.
# In a real app, you would centralize this logic.
async def get_current_admin_user(user: dict = Depends(get_current_user)):
    # This check assumes the JWT role claim is reliable.
    # For a global admin, the JWT should be issued by a separate, global auth system.
    # For simplicity, we check the role from a standard tenant JWT.
    if user.get("role") != UserRole.ROLE_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
    return user

# All routes in this file are for super admin operations.
# They should be protected and operate on the public schema.
router = APIRouter(
    prefix="/admin/reserved-subdomains", 
    tags=["Admin - Reserved Subdomains"],
    dependencies=[Depends(get_current_admin_user)] # Apply security to all routes in this router
)

@router.post("/", response_model=ReservedSubdomainRead, status_code=status.HTTP_201_CREATED)
async def create_reserved_subdomain(
    data: ReservedSubdomainCreate,
    db: AsyncSession = Depends(get_db_public)
):
    """
    Reserve a new subdomain. Only accessible by admins.
    """
    service = ReservedSubdomainService(db)
    return await service.create_subdomain(data)

@router.get("/", response_model=List[ReservedSubdomainRead])
async def get_all_reserved_subdomains(db: AsyncSession = Depends(get_db_public)):
    """
    Get a list of all reserved subdomains. Only accessible by admins.
    """
    service = ReservedSubdomainService(db)
    return await service.get_all_subdomains()

@router.get("/{subdomain_id}", response_model=ReservedSubdomainRead)
async def get_reserved_subdomain(subdomain_id: str, db: AsyncSession = Depends(get_db_public)):
    """
    Get a single reserved subdomain by its ID. Only accessible by admins.
    """
    service = ReservedSubdomainService(db)
    return await service.get_subdomain_by_id(subdomain_id)

@router.patch("/{subdomain_id}", response_model=ReservedSubdomainRead)
async def update_reserved_subdomain(
    subdomain_id: str,
    data: ReservedSubdomainUpdate,
    db: AsyncSession = Depends(get_db_public)
):
    """
    Update a reserved subdomain's details. Only accessible by admins.
    """
    service = ReservedSubdomainService(db)
    return await service.update_subdomain(subdomain_id, data)

@router.delete("/{subdomain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reserved_subdomain(subdomain_id: str, db: AsyncSession = Depends(get_db_public)):
    """
    Delete a reserved subdomain. Only accessible by admins.
    """
    service = ReservedSubdomainService(db)
    await service.delete_subdomain(subdomain_id)
    return None 

