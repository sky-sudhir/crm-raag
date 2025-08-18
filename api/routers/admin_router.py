from fastapi import APIRouter, Depends, HTTPException
# File: api/routers/admin_router.py
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.tenant import get_db_public
from api.services.onboarding_service import OnboardingService
from api.utils.response import create_response

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/sync-tenants", summary="Sync all tenant schemas with the latest tables")
async def sync_tenant_schemas(db: AsyncSession = Depends(get_db_public)):
    """
    This endpoint iterates through all registered tenants and creates any
    missing tables in their schemas. Useful after deploying a new feature
    that requires a new table.
    """
    # This endpoint should be protected by super-admin authentication in a real app.
    onboarding_service = OnboardingService(db)
    synced_schemas = await onboarding_service.sync_all_tenants()
    
    return create_response(
        message=f"Successfully synced {len(synced_schemas)} tenant schemas.",
        data={"synced_schemas": synced_schemas}
    )