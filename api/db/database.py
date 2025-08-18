from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from api.config import DATABASE_URL

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_unscoped_db_session() -> AsyncSession:
    """
    Provides a neutral, unscoped database session.
    
    WARNING: This session is NOT schema-aware. It should ONLY be used for
    the special case of the onboarding transaction where operations need
    to happen across both the public and a new tenant schema.
    """
    async with AsyncSessionLocal() as session:
        yield session