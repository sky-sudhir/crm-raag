from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.response_class import APIResponse
from src.feature.user.schema import UserResponseModel
from src.feature.user.service import UserService
from src.db.main import get_session

user_router = APIRouter(prefix="/users", tags=["User"])

@user_router.get("/", response_model=APIResponse)
async def get_users(session: AsyncSession = Depends(get_session)):
    return await UserService(session).get_all_users()
