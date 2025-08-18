# File: api/middleware/tenant.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, text
from api.db.tenant import tenant_schema 
from api.db.database import AsyncSessionLocal 
from api.models.organization import Organization 

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get hostname from the request, e.g., "orange.localhost" or "localhost"
        # print("Request hostname:", request.headers.get("hostname"))
        hostname = request.headers.get("host", "").split(":")[0]
        # hostname = "orange"
        
        print("hostname", hostname)
        # This is your main domain for public operations like signup.
        # In production, this would be your main app domain.
        main_domain = "localhost" # Use "localhost" if you test in a browser

        print("main_domain", main_domain)
        print("hostname == main_domain", hostname == main_domain)
        # If the request is for the main domain, it's a Public Request.
        # We do nothing and let it pass. Its endpoints will use get_db_public_session.
        if hostname == main_domain:
            return await call_next(request)

        # --- If we are here, it's a subdomain request. This is the tenant logic. ---

        # 1. Extract the subdomain from the hostname.
        subdomain = hostname.split(".")[0]

        print("subdomain", subdomain)
        
        # CRITICAL: Validate that this is a real tenant by looking up its subdomain.
        # We create a temporary, short-lived session that is hardcoded to the 
        # public schema just for this one lookup. This is a vital security check.
        async with AsyncSessionLocal() as session:
            # Ensure we are querying the public schema
            await session.execute(text('SET search_path TO "public"'))
            
            # 2. Find the organization record using the `subdomain` field.
            stmt = select(Organization).where(Organization.subdomain == subdomain)
            result = await session.execute(stmt)
            organization = result.scalar_one_or_none()

            print("organization", organization)

            if not organization:
                # If no organization is found for this subdomain, stop the request.
                raise HTTPException(status_code=404, detail=f"Workspace with subdomain '{subdomain}' not found.")
            
            # 3. Retrieve the correct schema name from the organization record.
            schema_name = organization.schema

        # 4. The "message passing": We set the schema name in the ContextVar.
        # This makes it available to the `get_db_tenant_session` dependency.
        token = tenant_schema.set(schema_name)
        print("subdomain", subdomain)

        
        # Now, we let the request proceed to the actual endpoint.
        response = await call_next(request)
        
        # After the request is done, we clean up the ContextVar.
        tenant_schema.reset(token)
        
        return response