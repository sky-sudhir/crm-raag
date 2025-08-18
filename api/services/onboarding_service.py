from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from api.db.database import Base
from api.models.organization import Organization

class OnboardingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_tenant_models(self):
        """
        Dynamically gets all SQLAlchemy Table objects that are NOT in the public schema.
        These are the tables that need to be created for each new tenant.
        """
        tenant_tables = []
        for table in Base.metadata.sorted_tables:
            if table.schema != "public":
                tenant_tables.append(table)
        return tenant_tables

    async def provision_tenant(self, schema_name: str):
        """
        Creates a new schema and all tenant-specific tables within it.
        """
        # Create the schema
        await self.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

        # Get the list of table blueprints to create
        tenant_tables = await self.get_tenant_models()

        # Temporarily switch to the new schema to create tables
        await self.session.execute(text(f'SET search_path TO "{schema_name}"'))
        
        # Create all tenant-specific tables
        async with self.session.begin_nested():
            await self.session.run_sync(Base.metadata.create_all, tables=tenant_tables)
        
        # Revert search_path to public
        await self.session.execute(text('SET search_path TO "public"'))

    async def sync_all_tenants(self):
        """
        Ensures all existing tenants have all the latest tables.
        """
        # Get all tenant schemas from the public organizations table
        result = await self.session.execute(select(Organization.schema))
        all_schemas = result.scalars().all()
        
        # Get the list of table blueprints that should exist for every tenant
        tenant_tables = await self.get_tenant_models()

        synced_schemas = []
        for schema_name in all_schemas:
            # For each tenant, switch to their schema
            await self.session.execute(text(f'SET search_path TO "{schema_name}"'))
            # Run create_all with checkfirst=True, which only creates missing tables
            async with self.session.begin_nested():
                await self.session.run_sync(Base.metadata.create_all, tables=tenant_tables, checkfirst=True)
            synced_schemas.append(schema_name)
        
        # Revert search_path to public
        await self.session.execute(text('SET search_path TO "public"'))
        return synced_schemas