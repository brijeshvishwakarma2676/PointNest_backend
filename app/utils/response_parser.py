from typing import Any, Optional
from app.core.exceptions import APIException


def generate_response(
    status_code: int, message: str, data: Optional[Any] = None, success: bool = False
) -> APIException:
    """
    Returns an APIException that can be raised in a route.
    A custom exception handler will catch this and return the flat JSON structure.
    """
    return APIException(
        status_code=status_code,
        message=message,
        data=data if data is not None else [],
        success=success,
    )


def success_response(
    message: str,
    data: Optional[Any] = None,
) -> dict:
    """
    Returns a standard dictionary to be used for 200/201 Success responses.
    """
    return {
        "success": True,
        "message": message,
        "data": data if data is not None else [],
    }
