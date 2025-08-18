# api/models/otp.py
from turtle import up
import uuid
from datetime import datetime, timedelta
from venv import create
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from api.db.database import Base

class OTP(Base):
    __tablename__ = "otp"
    __table_args__ = {"schema": "public"}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    otp = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.now() + timedelta(minutes=5))  # ✅ OTP expires in 5 min
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
