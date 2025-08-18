# api/models/dynamic_models.py
from sqlalchemy.orm import declarative_base
from api.models.user import UserRole

def get_user_model(schema: str):
    Base = declarative_base()

    class User(Base):
        __tablename__ = "users"
        __table_args__ = {"schema": schema}

    return User
