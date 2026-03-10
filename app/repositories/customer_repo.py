from sqlalchemy import or_
from app.models.customer import Customer


def create_customer(db, data):
    customer = Customer(**data)

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customer_by_contact(db, shop_id, phone=None, email=None):

    return (
        db.query(Customer)
        .filter(
            Customer.shop_id == shop_id,
            or_(Customer.phone == phone, Customer.email == email),
        )
        .first()
    )


def get_customers(db, shop_id, search_query=None, skip=0, limit=10):
    query = db.query(Customer).filter(Customer.shop_id == shop_id)

    if search_query:
        query = query.filter(
            or_(
                Customer.name.ilike(f"%{search_query}%"),
                Customer.phone.ilike(f"%{search_query}%"),
                Customer.email.ilike(f"%{search_query}%"),
            )
        )

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return total, items
