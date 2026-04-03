from sqlalchemy.orm import Session
from app.models.purchase import Purchase
from app.models.customer import Customer

def get_recent_purchases(db: Session, shop_id: int, page: int = 1, size: int = 10):
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
        .filter(Purchase.shop_id == shop_id, Purchase.is_active == 1)
        .order_by(Purchase.created_at.desc())
    )

    total = query.count()
    rows = query.offset((page - 1) * size).limit(size).all()
    
    # Convert Row objects to dictionaries for JSON serialization
    items = [row._asdict() for row in rows]

    return {"items": items, "total": total, "page": page, "size": size}
