# api/utils/security.py
from datetime import timedelta, timezone
from datetime import datetime
from uuid import UUID
from passlib.context import CryptContext
import jwt

from api.config import JWT_SECRET_KEY
from api.schemas.user import UserRole
# bcrypt context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)




def create_jwt_token(
    user_id: UUID,
    email: str,
    role: UserRole,
    tenant: str,
    expires_delta: timedelta = timedelta(minutes=60)
) -> str:
   
    secret_key = JWT_SECRET_KEY
    issue_time = datetime.now(timezone.utc)
    expire_time = issue_time + expires_delta

    # Construct the payload with standard and custom claims
    payload = {
        # Standard claims
        "iat": issue_time,         
        "exp": expire_time,        
        "sub": str(user_id), 

        # Custom claims based on your schema
        "tenant": tenant,
        "email": email,
        "role": role.value,         
    }

    encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256")
    
    return encoded_jwt


from fastapi import HTTPException, status
import jwt

def decode_jwt_token(token: str) -> dict:
    """Decode a JWT token and return the payload."""
    print("Decoding JWT token...",token,JWT_SECRET_KEY)
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
