from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.redemption import Redemption
from app.models.customer import Customer
from app.utils.datetime_utils import get_ist_now


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
        return None, None


def create_redemption(
    db: Session,
    shop_id: int,
    customer_id: int,
    points_used: int,
    amount_discounted: int,
):
    redemption = Redemption(
        shop_id=shop_id,
        customer_id=customer_id,
        points_used=points_used,
        amount_discounted=amount_discounted,
    )
    db.add(redemption)
    db.commit()
    db.refresh(redemption)
    return redemption


def get_redemptions_by_shop(
    db: Session,
    shop_id: int,
    page: int = 1,
    size: int = 20,
    date_filter: str = "all",
):
    base_filters = [Redemption.shop_id == shop_id, Redemption.is_active == 1]

    start_dt, end_dt = _get_date_range(date_filter)
    if start_dt and end_dt:
        base_filters += [
            Redemption.created_at >= start_dt,
            Redemption.created_at <= end_dt,
        ]

    query = (
        db.query(
            Redemption.id,
            Redemption.shop_id,
            Redemption.customer_id,
            Redemption.points_used,
            Redemption.amount_discounted,
            Redemption.created_at,
            Customer.name.label("customer_name"),
            Customer.phone.label("customer_phone"),
        )
        .join(Customer, Redemption.customer_id == Customer.id)
        .filter(*base_filters)
        .order_by(Redemption.created_at.desc())
    )

    total = query.count()
    rows = query.offset((page - 1) * size).limit(size).all()

    items = [row._asdict() for row in rows]

    return {"items": items, "total": total, "page": page, "size": size}
