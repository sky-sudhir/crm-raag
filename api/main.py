import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
from api.db.database import Base, engine

# Import all routers
from api.routers import user_router
from api.utils.util_error import ErrorResponse
from api.middleware.tenant import TenantMiddleware
from api.routers import user_router, auth as auth_router, admin_router, chat_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="CRM APP",
    description="CRM APP",
    version="3.0.0",
    lifespan=lifespan
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
app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(admin_router.router) 
app.include_router(chat_router.router)