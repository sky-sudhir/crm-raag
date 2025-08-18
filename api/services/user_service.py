import datetime
import random
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.organization import Organization
from api.models.otp import OTP
from api.models.user import User
from api.schemas.user import UserRead
from api.utils.email_sender import send_email
from api.utils.util_response import APIResponse

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    
    async def get_user_by_email(self, email: str)->UserRead:
        print("Current user:", email)

        result = await self.session.execute(select(User).where(User.email == email))
        result= result.scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return UserRead.model_validate(result) if result else None
