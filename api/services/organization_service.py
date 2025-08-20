from sqlalchemy.ext.asyncio import AsyncSession

from api.models.organization import Organization
from api.schemas.organization import CreateOrganizationRequest

class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_organization(self, organization: CreateOrganizationRequest):
        new_org = Organization(
            name=organization.name,
            email=organization.email,
            subdomain=organization.subdomain,
            schema_name=organization.schema_name
        )
        self.session.add(new_org)
        await self.session.commit()
        return new_org
