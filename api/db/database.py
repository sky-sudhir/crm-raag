from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from api.config import DATABASE_URL  # ✅ load from env

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
