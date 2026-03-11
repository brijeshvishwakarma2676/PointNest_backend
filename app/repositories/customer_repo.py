from sqlalchemy import or_
from app.models.customer import Customer


def create_customer(db, data):
    customer = Customer(**data)

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customer_by_contact(db, shop_id, phone=None, email=None):
    conditions = []
    if phone:
        conditions.append(Customer.phone == phone)
    if email:
        conditions.append(Customer.email == email)

    if not conditions:
        return None

    return (
        db.query(Customer)
        .filter(
            Customer.shop_id == shop_id,
            Customer.is_active == 1,
            or_(*conditions),
        )
        .first()
    )


def get_customers(db, shop_id, search_query=None, skip=0, limit=10):
    query = db.query(Customer).filter(
        Customer.shop_id == shop_id, Customer.is_active == 1
    )

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


def get_customer_by_id(db, shop_id, customer_id):
    return (
        db.query(Customer)
        .filter(
            Customer.shop_id == shop_id,
            Customer.id == customer_id,
            Customer.is_active == 1,
        )
        .first()
    )
