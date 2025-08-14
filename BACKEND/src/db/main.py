
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

# Base class for SQLAlchemy models
Base = declarative_base()



# Async engine
async_engine = create_async_engine(
    url=settings.POSTGRES_URL,
    echo=True,
)

# Async session factory
async_session = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency for FastAPI
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# DB init (create tables)
async def init_db():
    from .models import User  # Import models here so metadata is ready
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
