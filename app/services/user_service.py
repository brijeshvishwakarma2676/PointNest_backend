from fastapi import status
from app.core.security import hash_password, verify_password
from app.core.auth import create_access_token, create_refresh_token
from app.repositories import user_repo
from app.utils import response_parser
from app.core import messages


def register_user(db, data):
    existing_user = user_repo.get_existing_user(
        db, data["email"], data["phone"], data["shop_name"]
    )

    if existing_user:
        if existing_user.email == data["email"]:
            raise response_parser.generate_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=messages.EMAIL_ALREADY_EXISTS,
                success=False,
            )
        if existing_user.phone == data["phone"]:
            raise response_parser.generate_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=messages.PHONE_ALREADY_EXISTS,
                success=False,
            )
        if existing_user.shop_name == data["shop_name"]:
            raise response_parser.generate_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=messages.SHOP_NAME_ALREADY_EXISTS,
                success=False,
            )

    data["password"] = hash_password(data["password"])
    return user_repo.create_user(db, data)


def login_user(db, email, password):
    user = user_repo.get_user_by_email(db, email)

    if not user:
        raise response_parser.generate_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=messages.INVALID_CREDENTIALS,
            success=False,
        )

    if not verify_password(password, user.password):
        raise response_parser.generate_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=messages.INVALID_CREDENTIALS,
            success=False,
        )

    token_data = {"user_id": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return response_parser.success_response(
        message=messages.LOGIN_SUCCESSFULLY,
        data={"access_token": access_token, "refresh_token": refresh_token},
    )
