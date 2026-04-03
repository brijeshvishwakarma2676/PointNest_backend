from sqlalchemy.orm import Session
from app.models.redemption import Redemption
from app.models.customer import Customer


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


def get_redemptions_by_shop(db: Session, shop_id: int, page: int = 1, size: int = 20):
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
        .filter(Redemption.shop_id == shop_id, Redemption.is_active == 1)
        .order_by(Redemption.created_at.desc())
    )

    total = query.count()
    rows = query.offset((page - 1) * size).limit(size).all()
    
    # Convert Row objects to dictionaries for JSON serialization
    items = [row._asdict() for row in rows]

    return {"items": items, "total": total, "page": page, "size": size}
