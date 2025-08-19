from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from api.db.database import Base
from api.models.organization import Organization
from api.utils.TenantUtils import TenantUtils

class OnboardingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # async def provision_tenant(self, schema_name: str):
    #     """
    #     Creates a new schema and all tenant-specific tables within it.
    #     """
    #     # Create the schema
    #     await self.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

    #     # Get the list of table blueprints to create
    #     tenant_tables = self.get_tenant_models()

    #     # --- THIS IS THE CRITICAL FIX ---
    #     # We use `begin_nested` on the session itself. This creates a SAVEPOINT.
    #     # When this block finishes, the DDL commands are flushed to the DB
    #     # and the new tables become visible to the parent transaction.
    #     async with self.session.begin_nested():
    #         # Get the underlying connection to run the DDL command
    #         connection = await self.session.connection()
    #         await connection.run_sync(
    #             Base.metadata.create_all, tables=tenant_tables
    #         )
        
    async def sync_all_tenants(self):
        """
        Ensures all existing tenants have all the latest tables.
        """
        # Get all tenant schemas from the public organizations table
        result = await self.session.execute(select(Organization.schema))
        all_schemas = result.scalars().all()
        
        # Get the list of table blueprints that should exist for every tenant
        tenant_tables = TenantUtils.get_tenant_tables()

        # Get the underlying connection once
        connection = await self.session.connection()
        
        synced_schemas = []
        for schema_name in all_schemas:
            # For each tenant, switch to their schema
            await self.session.execute(text(f'SET search_path TO "{schema_name}"'))
            
            # Run create_all on the connection
            await connection.run_sync(
                Base.metadata.create_all, tables=tenant_tables, checkfirst=True
            )
            synced_schemas.append(schema_name)
        
        # Revert search_path to public
        await self.session.execute(text('SET search_path TO "public"'))
        return synced_schemas