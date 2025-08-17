from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Postgres URL format:
# postgresql+asyncpg://username:password@host:port/dbname
DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost:5432/service1"

class Base(DeclarativeBase):
    pass

# Engine & session factory
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
