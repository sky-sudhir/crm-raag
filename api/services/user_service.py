import datetime
import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.organization import Organization
from api.models.otp import OTP
from api.utils.email_sender import send_email
from api.utils.util_response import APIResponse

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    
    # async def signup(self, email: str):
    #     otp_code = random.randint(100000, 999999)
    #     expires_at = datetime.now() + datetime.timedelta(minutes=5)

    #     org= await self.session.execute(
    #         select(Organization).where(Organization.email == email)
    #     )

    #     org = org.scalar_one_or_none()

    #     if org:
    #         raise APIResponse(message="Organization already exists with this email").model_dump()

    #     # Check if email already exists in OTP table
    #     result = await self.session.execute(select(OTP).where(OTP.email == email))
    #     otp_entry = result.scalar_one_or_none()

    #     if otp_entry:
    #         # Update existing OTP
    #         otp_entry.otp = otp_code
    #         otp_entry.expires_at = expires_at
    #     else:
    #         # Create new OTP record
    #         otp_entry = OTP(email=email, otp=otp_code, expires_at=expires_at)
    #         self.session.add(otp_entry)

    #     await self.session.commit()

    #     # Send OTP via email
    #     await send_email(email, otp_code)

    #     return APIResponse(message="OTP sent to email").model_dump()