# src/schemas/response.py
from typing import Any, List, Optional
from pydantic import BaseModel

class APIResponse(BaseModel):
    data: Optional[Any] = None
    total_count: Optional[int] = 0
    message: Optional[str]=""
    success: Optional[bool]=True


class ErrorResponse(BaseModel):
    stack: Optional[str]=""
    message: Optional[str]="Interal Server Error"
    success: Optional[bool]=False


