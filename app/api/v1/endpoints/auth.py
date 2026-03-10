import logging
from pydantic import ValidationError
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.schemas.user import UserRegister, UserResponse, UserLogin
from app.config.database import get_db
from app.services.user_service import register_user, login_user
from app.utils import response_parser
from app.core import messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    try:
        user = register_user(db, data.model_dump())
        response_data = UserResponse.model_validate(user).model_dump()
        return response_parser.success_response(
            message=messages.USER_REGISTERED_SUCCESSFULLY, data=response_data
        )

    except ValidationError as err:
        raise response_parser.generate_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=messages.VALIDATION_ERROR,
            data=err.errors(),
            success=False,
        )
    except Exception as err:
        if hasattr(err, "status_code"):
            raise err
        logger.exception(f"Some Error Occurred in register(): {err}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    try:
        token = login_user(db, data.email, data.password)
        return token  # user_service.py login_user already returns standard success_response
    except ValidationError as err:
        raise response_parser.generate_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=messages.VALIDATION_ERROR,
            data=err.errors(),
            success=False,
        )
    except Exception as err:
        if hasattr(err, "status_code"):
            raise err
        logger.exception(f"Some Error Occurred in login(): {err}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )
