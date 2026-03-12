from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.models.customer import Customer
from app.models.purchase import Purchase
from sqlalchemy.sql import func


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


def get_shop_metrics(db: Session, shop_id: int):
    total_customers = (
        db.query(Customer)
        .filter(Customer.shop_id == shop_id, Customer.is_active == 1)
        .count()
    )
    total_purchases = (
        db.query(Purchase)
        .filter(Purchase.shop_id == shop_id, Purchase.is_active == 1)
        .count()
    )
    total_points = (
        db.query(func.sum(Purchase.points_earned))
        .filter(Purchase.shop_id == shop_id, Purchase.is_active == 1)
        .scalar()
        or 0
    )
    total_revenue = (
        db.query(func.sum(Purchase.amount))
        .filter(Purchase.shop_id == shop_id, Purchase.is_active == 1)
        .scalar()
        or 0
    )

    return {
        "total_customers": total_customers,
        "total_purchases": total_purchases,
        "total_points_issued": total_points,
        "total_revenue": total_revenue,
    }
