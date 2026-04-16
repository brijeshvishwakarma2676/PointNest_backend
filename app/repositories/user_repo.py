from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app.models.user import User
from app.models.customer import Customer
from app.models.purchase import Purchase
from app.utils.datetime_utils import get_ist_now


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


def _get_date_range(date_filter: str):
    """
    Returns (start_dt, end_dt) tuple based on the filter keyword.
    Uses IST to match the database storage format.
    """
    now = get_ist_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if date_filter == "today":
        return today_start, now
    elif date_filter == "yesterday":
        yesterday_start = today_start - timedelta(days=1)
        return yesterday_start, today_start
    elif date_filter == "7days":
        return today_start - timedelta(days=7), now
    elif date_filter == "30days":
        return today_start - timedelta(days=30), now
    else:
        # "all" or any unknown value — no date filter
        return None, None


def get_shop_metrics(db: Session, shop_id: int, date_filter: str = "all"):
    start_dt, end_dt = _get_date_range(date_filter)

    # Total customers is always all-time
    total_customers = (
        db.query(Customer)
        .filter(Customer.shop_id == shop_id, Customer.is_active == 1)
        .count()
    )

    # Build purchase filters
    purchase_filters = [Purchase.shop_id == shop_id, Purchase.is_active == 1]
    if start_dt and end_dt:
        purchase_filters += [
            Purchase.created_at >= start_dt,
            Purchase.created_at <= end_dt,
        ]

    total_purchases = (
        db.query(Purchase)
        .filter(*purchase_filters)
        .count()
    )
    total_points = (
        db.query(func.sum(Purchase.points_earned))
        .filter(*purchase_filters)
        .scalar()
        or 0
    )
    total_revenue = (
        db.query(func.sum(Purchase.amount))
        .filter(*purchase_filters)
        .scalar()
        or 0
    )

    return {
        "total_customers": total_customers,
        "total_purchases": total_purchases,
        "total_points_issued": total_points,
        "total_revenue": total_revenue,
        "date_filter": date_filter,
    }
