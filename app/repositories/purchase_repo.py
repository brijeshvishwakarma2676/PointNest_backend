from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.purchase import Purchase
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


def get_recent_purchases(
    db: Session,
    shop_id: int,
    page: int = 1,
    size: int = 10,
    date_filter: str = "all",
):
    base_filters = [Purchase.shop_id == shop_id, Purchase.is_active == 1]

    start_dt, end_dt = _get_date_range(date_filter)
    if start_dt and end_dt:
        base_filters += [
            Purchase.created_at >= start_dt,
            Purchase.created_at <= end_dt,
        ]

    query = (
        db.query(
            Purchase.id,
            Purchase.shop_id,
            Purchase.customer_id,
            Purchase.amount,
            Purchase.points_earned,
            Purchase.created_at,
            Customer.name.label("customer_name"),
            Customer.phone.label("customer_phone"),
        )
        .join(Customer, Purchase.customer_id == Customer.id)
        .filter(*base_filters)
        .order_by(Purchase.created_at.desc())
    )

    total = query.count()
    rows = query.offset((page - 1) * size).limit(size).all()

    items = [row._asdict() for row in rows]

    return {"items": items, "total": total, "page": page, "size": size}
