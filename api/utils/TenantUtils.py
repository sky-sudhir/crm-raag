from typing import List
from sqlalchemy import Table
from api.db.database import Base

class TenantUtils:
    """Utility methods for handling tenant-related SQLAlchemy models."""

    @staticmethod
    def get_tenant_tables() -> List[Table]:
        """Return all non-public schema tables for tenants."""
        return [table for table in Base.metadata.sorted_tables if table.schema != "public"]
