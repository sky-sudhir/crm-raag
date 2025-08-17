# api/utils/response.py
from typing import Any, Optional
from api.utils.util_response import APIResponse

def create_response(
    data: Optional[Any] = None,
    message: str = "",
    success: bool = True,
    total_count: int = 0
) -> APIResponse:
    """
    Wrap response in a consistent APIResponse schema.
    """
    return APIResponse(
        data=data,
        message=message,
        success=success,
        total_count=total_count
    )
