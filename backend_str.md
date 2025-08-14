# Backend AI Agent Instructions

## 1. Folder Structure

- `src/`
  - `__init__.py` – FastAPI app initialization and router inclusion.
  - `config.py` – Loads environment variables using Pydantic Settings.
  - `db/`
    - `main.py` – SQLAlchemy async engine/session setup, `init_db`, and `get_session`.
    - `models.py` – SQLAlchemy models (e.g., `User`, `RoleEnum`).
  - `feature/`
    - `user/`
      - `routes.py` – FastAPI router for user endpoints.
      - `service.py` – Business logic for user operations.
      - `schema.py` – Pydantic models for user API responses.
  - `utils/`
    - `response_class.py` – Defines the `APIResponse` class for standardized API responses.

## 2. How to Use Classes

### APIResponse

- raise Exception class for 500 error and HTTPException from fastapi for other errors 400,401,403 etc

- Defined in [`src/utils/response_class.py`](src/utils/response_class.py).
- Used as the standard response model for all API endpoints.
- Example usage in a service:

  ```python
  from src.utils.response_class import APIResponse

  # In a service method
  return APIResponse(
      data=users,
      total_count=len(users),
      message="Users fetched successfully",
      success=True
  )
  ```

- In a route, set `response_model=APIResponse` and return the result from the service.

### UserService

- Defined in [`src/feature/user/service.py`](src/feature/user/service.py).
- Accepts an `AsyncSession` in the constructor.
- Provides methods like `get_all_users()` that return an `APIResponse`.
- Example usage in a route:

  ```python
  from src.feature.user.service import UserService

  @user_router.get("/", response_model=APIResponse)
  async def get_users(session: AsyncSession = Depends(get_session)):
      return await UserService(session).get_all_users()
  ```

### UserResponseModel

- Defined in [`src/feature/user/schema.py`](src/feature/user/schema.py).
- Used for serializing user data in API responses.
- Set as the type for the `data` field in `APIResponse` when returning user lists.

## 3. API Endpoint Example

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.response_class import APIResponse
from src.feature.user.service import UserService
from src.db.main import get_session

user_router = APIRouter(prefix="/users", tags=["User"])

@user_router.get("/", response_model=APIResponse)
async def get_users(session: AsyncSession = Depends(get_session)):
    return await UserService(session).get_all_users()
```

## 4. Best Practices

- Always use `APIResponse` for endpoint responses for consistency.
- raise Exception class for 500 error and HTTPException from fastapi for other errors 400,401,403 etc.
- Place business logic in service classes, not in routes.
- Use Pydantic models for all request/response schemas.
- Use dependency injection (`Depends(get_session)`) for database sessions.
- Organize features by domain (e.g., `feature/user/`).

---
