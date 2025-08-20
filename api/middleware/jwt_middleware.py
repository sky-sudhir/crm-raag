from contextvars import ContextVar
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from fastapi import Depends, FastAPI, Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from api import config
from api.utils.security import decode_jwt_token
from api.db.tenant import tenant_schema

# --- Configuration ---

SECRET_KEY = config.JWT_SECRET_KEY
ALGORITHM = "HS256"

reusable_oauth2 = HTTPBearer(
    scheme_name="Bearer",
    description="Enter your JWT token in the format 'Bearer <token>'",
    auto_error=False  # We will handle errors manually to provide custom messages
)

async def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(reusable_oauth2),
) -> dict:
    """
    A dependency to validate the JWT token and return the user payload.
    This will be applied to the router.
    """
    if auth is None or auth.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    remove_bearer = "Bearer "
    token = auth.credentials[len(remove_bearer):] if auth.credentials.startswith(remove_bearer) else auth.credentials
    try:
        payload = decode_jwt_token(token=token)
        current_schema=tenant_schema.get()
        if current_schema!=payload.get("tenant"):
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        # Catches any other JWT-related error (invalid signature, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    