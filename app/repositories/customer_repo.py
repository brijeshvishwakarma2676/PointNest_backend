from sqlalchemy import or_
from app.models.customer import Customer


def create_customer(db, data):
    customer = Customer(**data)

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customer_by_contact(db, shop_id, phone=None, email=None):

    return db.query(Customer).filter(
        Customer.shop_id == shop_id,
        or_(
            Customer.phone == phone,
            Customer.email == email
        )
    ).first()