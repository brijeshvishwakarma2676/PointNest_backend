import logging
from pydantic import ValidationError
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.schemas.user import UserRegister, UserResponse, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, VerifyOtpRequest
from app.core.auth import create_access_token, create_refresh_token
from jose import jwt, JWTError
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


@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        from app.config.settings import settings

        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("scope") != "refresh":
            raise response_parser.generate_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid token scope",
                success=False,
            )

        user_id = payload.get("user_id")
        if not user_id:
            raise response_parser.generate_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid token payload",
                success=False,
            )

        new_access_token = create_access_token({"user_id": user_id})

        return response_parser.success_response(
            message=messages.TOKEN_REFRESHED_SUCCESSFULLY,
            data={"access_token": new_access_token},
        )

    except JWTError:
        raise response_parser.generate_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid or expired refresh token",
            success=False,
        )
    except Exception as err:
        logger.exception(f"Some Error Occurred in refresh_token(): {err}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        from app.models.user import User, PasswordReset
        
        # Check if user exists
        user = db.query(User).filter(User.email == data.email, User.is_active == 1).first()
        if not user:
            raise response_parser.generate_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Registered access profile (email) not found.",
                success=False,
            )

        # Generate a secure 6-digit numeric OTP
        import random
        otp_code = f"{random.randint(100000, 999999)}"

        # Save the OTP in password_resets
        from app.utils.datetime_utils import get_ist_now
        from datetime import timedelta
        
        # Delete any existing reset requests for this email to keep table clean
        db.query(PasswordReset).filter(PasswordReset.email == data.email).delete()

        reset_req = PasswordReset(
            email=data.email,
            otp=otp_code,
            expires_at=get_ist_now() + timedelta(minutes=10)
        )
        db.add(reset_req)
        db.commit()

        # Send the OTP validation email via background tasks
        from app.services.email_service import send_otp_email
        send_otp_email(
            background_tasks=background_tasks,
            recipient_email=data.email,
            otp_code=otp_code,
            owner_name=user.owner_name or "PointNest Partner"
        )

        return response_parser.success_response(
            message="Verification OTP code successfully dispatched to your email."
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
        logger.exception(f"Some Error Occurred in forgot_password(): {err}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    try:
        from app.models.user import User, PasswordReset
        from app.utils.datetime_utils import get_ist_now
        from app.config.settings import settings
        
        # Verify the OTP and expiration (bypass if matching the configured static OTP)
        is_static_valid = settings.STATIC_OTP and data.otp == settings.STATIC_OTP
        
        if not is_static_valid:
            reset_req = db.query(PasswordReset).filter(
                PasswordReset.email == data.email,
                PasswordReset.otp == data.otp,
                PasswordReset.expires_at >= get_ist_now()
            ).first()

            if not reset_req:
                raise response_parser.generate_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Invalid or expired verification OTP code.",
                    success=False,
                )


        # Retrieve the user record
        user = db.query(User).filter(User.email == data.email, User.is_active == 1).first()
        if not user:
            raise response_parser.generate_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User profile no longer active or exists.",
                success=False,
            )

        # Hash and update the user's password
        from app.core.security import hash_password
        user.password = hash_password(data.new_password)
        
        # Clean up all password reset records for this email
        db.query(PasswordReset).filter(PasswordReset.email == data.email).delete()
        
        db.commit()

        return response_parser.success_response(
            message="Your partner terminal authorization key has been successfully updated."
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
        logger.exception(f"Some Error Occurred in reset_password(): {err}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )


@router.post("/verify-otp")
def verify_otp(
    data: VerifyOtpRequest,
    db: Session = Depends(get_db)
):
    try:
        from app.models.user import PasswordReset
        from app.utils.datetime_utils import get_ist_now
        from app.config.settings import settings
        
        # Verify the OTP and expiration (bypass if matching the configured static OTP)
        is_static_valid = settings.STATIC_OTP and data.otp == settings.STATIC_OTP
        
        if not is_static_valid:
            reset_req = db.query(PasswordReset).filter(
                PasswordReset.email == data.email,
                PasswordReset.otp == data.otp,
                PasswordReset.expires_at >= get_ist_now()
            ).first()

            if not reset_req:
                raise response_parser.generate_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Invalid or expired verification OTP code.",
                    success=False,
                )

        return response_parser.success_response(
            message="Verification OTP code successfully verified."
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
        logger.exception(f"Some Error Occurred in verify_otp(): {err}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )


