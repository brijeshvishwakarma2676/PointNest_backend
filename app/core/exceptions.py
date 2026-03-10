from typing import Any


class APIException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        data: Any = None,
        success: bool = False,
    ):
        self.status_code = status_code
        self.message = message
        self.data = data if data is not None else []
        self.success = success
