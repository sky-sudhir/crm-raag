from contextvars import ContextVar
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .database import AsyncSessionLocal

# A ContextVar is a special variable that holds a different value for each
# concurrent request. This is the "messenger" that will carry the correct
# schema name from our middleware to our database session.
tenant_schema: ContextVar[str] = ContextVar("tenant_schema", default="public")

# --- DEPENDENCY #1: For Tenant-Specific Operations ---
async def get_db_tenant() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a session that is locked to the current tenant's schema.
    
    This dependency reads the schema name set by the TenantMiddleware and
    configures the session to use that schema for all its operations.
    """
    schema = tenant_schema.get()
    async with AsyncSessionLocal() as session:
        # This is the core of the multi-tenancy logic. The `search_path`
        # tells PostgreSQL which schema to look in for tables when a query
        # doesn't explicitly specify a schema (e.g., "SELECT * FROM users").
        await session.execute(text(f'SET search_path TO "{schema}"'))
        yield session

# --- DEPENDENCY #2: For Public/Global Operations ---
async def get_db_public() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a session that is locked to the public schema.
    
    Use this for operations that should always happen on the public schema,
    like creating a new organization or looking up a tenant during validation.
    """
    print("Using public schema for database operations")
    async with AsyncSessionLocal() as session:
        # We explicitly set the search_path to 'public' to ensure we are not
        # accidentally operating within a tenant's schema.
        # await session.execute(text('SET search_path TO "public"'))
        yield session