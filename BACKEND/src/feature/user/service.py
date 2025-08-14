from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.response_class import APIResponse
from src.db.models import User

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_users(self):
        statement = select(User).order_by(User.created_at)
        result = await self.session.execute(statement)
        users= result.scalars().all()

        if len(users)==0:
            raise Exception()

        return APIResponse(
            data=users,
            total_count=len(users),
            message="Users fetched successfully",
            success=True
        )
