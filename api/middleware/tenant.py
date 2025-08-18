# File: api/middleware/tenant.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, text
from api.db.tenant import tenant_schema 
from api.db.database import AsyncSessionLocal 
from api.models.organization import Organization 
class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        hostname = request.headers.get("host", "").split(":")[0]
        
        print("hostname", hostname)
        main_domain = "localhost" # Use "localhost" if you test in a browser
        print("main_domain", main_domain)
        print("hostname == main_domain", hostname == main_domain)
        if hostname == main_domain:
            return await call_next(request)
        subdomain = hostname.split(".")[0]
        print("subdomain", subdomain)
        async with AsyncSessionLocal() as session:
            await session.execute(text('SET search_path TO "public"'))
            stmt = select(Organization).where(Organization.subdomain == subdomain)
            result = await session.execute(stmt)
            organization = result.scalar_one_or_none()
            print("organization", organization)
            if not organization:
                raise HTTPException(status_code=404, detail=f"Workspace with subdomain '{subdomain}' not found.")
            schema_name = organization.schema
        token = tenant_schema.set(schema_name)
        response = await call_next(request)
        tenant_schema.reset(token)
        return response