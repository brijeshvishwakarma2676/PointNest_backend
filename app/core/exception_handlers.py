import json
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import APIException
from app.core import messages

logger = logging.getLogger(__name__)


def add_exception_handlers(app: FastAPI):
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        data_str = json.dumps(exc.data, indent=2) if exc.data else "[]"
        logger.error(
            f"API Error - Path: [{request.method}] {request.url.path}\nStatus: {exc.status_code}, Message: {exc.message}\nData: {data_str}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": exc.success, "message": exc.message, "data": exc.data},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors_str = json.dumps(exc.errors(), indent=2)
        logger.error(
            f"Validation Error - Path: [{request.method}] {request.url.path}\nErrors: {errors_str}"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": messages.VALIDATION_ERROR,
                "data": exc.errors(),
            },
        )
