import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
from api.db.database import Base, engine

from api.routers.user import router as user_router
from api.routers.auth import router as auth_router
from api.routers.chat_router import router as chat_router
from api.routers.admin_router import router as admin_router
from api.routers.rag_router import router as rag_router
from api.utils.util_error import ErrorResponse
from api.middleware.tenant import TenantMiddleware
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On application startup, create only the tables that belong to the public schema.
    Tenant-specific tables are created dynamically during the onboarding process.
    """
    async with engine.begin() as conn:
        public_tables = [
            table for table in Base.metadata.sorted_tables if table.schema == "public"
        ]
        await conn.run_sync(Base.metadata.create_all, tables=public_tables)
    yield

# ... (the rest of your main.py file is unchanged) ...
app = FastAPI(
    title="CRM APP",
    description="CRM APP",
    version="3.0.0",
    lifespan=lifespan
)
# origins = [
#     "http://localhost:3000",   # React local dev
#     "http://127.0.0.1:3000",  # sometimes needed separately
#     "https://yourfrontend.com"  # production domain
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],            # allow all HTTP methods
    allow_headers=["*"],            # allow all headers
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
    # logging.error(f"Unhandled exception: {exc}", exc_info=True)
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

# Include all routers
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(admin_router) 
app.include_router(chat_router)
app.include_router(rag_router)
