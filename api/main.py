import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
from api.db.database import Base, engine

from api.routers.user_router import router as user_router
from api.routers.auth_router import router as auth_router
from api.routers.chat_router import router as chat_router
from api.routers.admin_router import router as admin_router
from api.routers.category_router import router as category_router
from api.utils.util_error import ErrorResponse
from api.middleware.tenant import TenantMiddleware
from fastapi.middleware.cors import CORSMiddleware
from api.models.knowledge_base import KnowledgeBase
from api.models.audit_log import AuditLogBase
from api.routers.reserved_subdomain_router import router as reserved_subdomain_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On application startup, create only the tables that belong to the public schema.
    Tenant-specific tables are created dynamically during the onboarding process.
    """
    async with engine.begin() as conn:
        # Create enum types first before creating tables
        await conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                    CREATE TYPE public.userrole AS ENUM ('ROLE_USER', 'ROLE_ADMIN');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'orgstatus') THEN
                    CREATE TYPE public.orgstatus AS ENUM ('ACTIVE', 'INACTIVE');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ragtype') THEN
                    CREATE TYPE public.ragtype AS ENUM ('BASIC', 'ADVANCED');
                END IF;
            END $$;
        """))
        
        # Now create tables
        public_tables = [
            table for table in Base.metadata.sorted_tables if table.schema == "public"
        ]
        await conn.run_sync(Base.metadata.create_all, tables=public_tables)
    yield

app = FastAPI(
    title="CRM APP",
    description="CRM APP",
    version="3.0.0",
    lifespan=lifespan
)

origin_regex = r"^https?:\/\/((localhost(:\d+)?)|([a-z0-9-]+\.redagent\.dev))$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Tenant-ID"],
)

app.add_middleware(TenantMiddleware)

@app.exception_handler(HTTPException)
async def global_exception_handler(request: Request, exc: HTTPException):
     return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            stack=None,
            message=exc.detail,
            success=False
        ).model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    stack_trace = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            stack=stack_trace,
            message="Interal Server Error",
            success=False
        ).model_dump()
    )

@app.get("/")
def home_page():
    return "I am up and running! 🚀"

@app.get("/health", include_in_schema=False)
async def health_check():
    """
    Health check endpoint for AWS ALB.
    Returns 200 OK when the service is healthy.
    """
    return JSONResponse(content={"status": "healthy"}, status_code=200)

# Include all routers
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(admin_router) 
app.include_router(chat_router)
app.include_router(category_router)
app.include_router(reserved_subdomain_router)
