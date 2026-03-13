from app.models.redemption import Redemption


def create_redemption(
    db, shop_id: int, customer_id: int, points_used: int, amount_discounted: int
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
