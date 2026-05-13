from app.repositories.customer_repo import (
    get_customer_by_contact,
    create_customer,
    get_customer_by_id,
    update_customer_details,
)


def get_or_create_customer(db, shop_id, data: dict):
    # Normalize empty strings to None for unique fields (phone/email)
    phone = data.get("phone") if data.get("phone") else None
    email = data.get("email") if data.get("email") else None
    
    # Update dictionary to ensure create_customer uses normalized values
    if "phone" in data and not data["phone"]:
        data["phone"] = None
    if "email" in data and not data["email"]:
        data["email"] = None

    customer = get_customer_by_contact(
        db, shop_id=shop_id, phone=phone, email=email
    )

    if customer:
        return customer, False

    return create_customer(db, data), True


def update_customer(db, shop_id, data: dict):
    # Normalize empty strings to None for unique fields
    if "phone" in data and not data["phone"]:
        data["phone"] = None
    if "email" in data and not data["email"]:
        data["email"] = None

    customer = get_customer_by_id(db, shop_id, data.get("id"))

    if not customer:
        return None

    return update_customer_details(db, customer, data)
