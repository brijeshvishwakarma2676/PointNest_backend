from app.repositories.customer_repo import (
    get_customer_by_contact,
    create_customer,
    get_customer_by_id,
    update_customer_details,
)


def get_or_create_customer(db, shop_id, data: dict):
    customer = get_customer_by_contact(
        db, shop_id=shop_id, phone=data.get("phone"), email=data.get("email")
    )

    if customer:
        return customer, False

    return create_customer(db, data), True


def update_customer(db, shop_id, data: dict):
    customer = get_customer_by_id(db, shop_id, data.get("id"))

    if not customer:
        return None

    return update_customer_details(db, customer, data)
