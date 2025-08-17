from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    data: Optional[Any] = None
    total_count: Optional[int] = 0
    message: Optional[str]=""
    success: Optional[bool]=True