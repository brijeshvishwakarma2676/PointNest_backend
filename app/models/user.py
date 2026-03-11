from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    shop_name = Column(String(255))
    owner_name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    password = Column(String(255))

    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
