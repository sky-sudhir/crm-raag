from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, text
from api.db.tenant import tenant_schema 
from api.db.database import AsyncSessionLocal 
from api.models.organization import Organization 

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # --- NEW LOGIC ---
        # Instead of the hostname, we now look for a custom header.
        # The frontend (e.g., medcamp.redagent.dev) is responsible for sending this.
        subdomain = request.headers.get("X-Tenant-ID")

        # If the header is not present, it's a bad request, as we can't identify the tenant.
        # We can make an exception for certain global routes if needed, but for now, we'll require it.
        if not subdomain:
            # You might want to allow certain paths (like /admin/...) to bypass this check
            # if they are truly global and don't require a tenant context.
            # For now, we assume most API calls are tenant-specific.
            # Returning an error is safer than defaulting to 'public'.
             return await call_next(request)


        async with AsyncSessionLocal() as session:
            # The database logic remains the same. We still look up the organization
            # in the public schema to get the actual schema name.
            await session.execute(text('SET search_path TO "public"'))
            stmt = select(Organization).where(Organization.subdomain == subdomain)
            result = await session.execute(stmt)
            organization = result.scalar_one_or_none()
            
            if not organization:
                raise HTTPException(status_code=404, detail=f"Workspace '{subdomain}' not found. Check the X-Tenant-ID header.")
            
            schema_name = organization.schema
        
        # Set the schema for this request's context
        token = tenant_schema.set(schema_name)
        response = await call_next(request)
        tenant_schema.reset(token)
        return response