from sqlalchemy import select
from fastapi import HTTPException
from api.db.database import Base
from api.models.user import get_user_model, UserRole
from api.models.organization import Organization
from api.utils.security import hash_password
from api.utils.util_response import APIResponse
from sqlalchemy.schema import CreateSchema
from sqlalchemy.exc import ProgrammingError


class SchemaManager:
    def __init__(self, session):
        self.session = session

    async def ensure_schema(self, schema_name: str):
        """Ensure schema exists (create if not)."""
        async with self.session.bind.begin() as conn:
            try:
                await conn.execute(CreateSchema(schema_name))
            except ProgrammingError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Schema '{schema_name}' already exists or cannot be created."
                )

    async def create_tables(self, models: list):
        """Create given models' tables."""
        async with self.session.bind.begin() as conn:
            for model in models:
                await conn.run_sync(Base.metadata.create_all, tables=[model.__table__])