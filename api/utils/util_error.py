from typing import Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    stack: Optional[str]=""
    message: Optional[str]="Interal Server Error"
    success: Optional[bool]=False