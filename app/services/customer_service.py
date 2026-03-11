from app.repositories.customer_repo import get_customer_by_contact, create_customer


def get_or_create_customer(db, shop_id, data: dict):

    customer = get_customer_by_contact(
        db, shop_id=shop_id, phone=data.get("phone"), email=data.get("email")
    )

    if customer:
        return customer, False

    return create_customer(db, data), True
