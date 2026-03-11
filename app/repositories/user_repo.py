from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email, User.is_active == 1).first()


def get_user_by_phone(db: Session, phone: str):
    return db.query(User).filter(User.phone == phone, User.is_active == 1).first()


def get_user_by_shop_name(db: Session, shop_name: str):
    return (
        db.query(User).filter(User.shop_name == shop_name, User.is_active == 1).first()
    )


def get_existing_user(db: Session, email: str, phone: str, shop_name: str):
    return (
        db.query(User)
        .filter(
            or_(User.email == email, User.phone == phone, User.shop_name == shop_name),
            User.is_active == 1,
        )
        .first()
    )


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id, User.is_active == 1).first()


def create_user(db: Session, data):
    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
