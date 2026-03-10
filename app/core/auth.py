from jose import jwt
from datetime import datetime, timedelta
from app.config.settings import settings

def create_access_token(data: dict):
    payload = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE
    )

    payload.update({"exp": expire})

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return token