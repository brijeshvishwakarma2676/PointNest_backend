from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.config.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    shop_id = Column(Integer, ForeignKey("users.id"))

    name = Column(String(255))

    phone = Column(String(20), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)

    points = Column(Integer, default=0)

    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
