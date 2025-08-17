from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager


# Import all models to ensure they are registered with Base
from api.db.database import Base, engine

# Import all routers
from api.routers import user_router

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

@app.get("/")
def home_page():
    return RedirectResponse("/docs")

# Include all routers
app.include_router(user_router.router)
