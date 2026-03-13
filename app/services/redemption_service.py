from app.config.settings import settings


def calculate_discount(points: int) -> int:
    """Convert points to INR discount value using configurable ratio from .env."""
    return points // settings.POINTS_PER_RUPEE


def redeem_points(db, customer, points_to_redeem: int, shop_id: int):
    from app.repositories.redemption_repo import create_redemption

    if customer.points < points_to_redeem:
        return None, "Insufficient points"

    discount = calculate_discount(points_to_redeem)

    # Deduct points from customer
    customer.points -= points_to_redeem

    # Persist the redemption record first (flush to get redemption.id)
    from app.repositories.redemption_repo import create_redemption
    from app.repositories.points_ledger_repo import add_ledger_entry

    redemption = create_redemption(
        db,
        shop_id=shop_id,
        customer_id=customer.id,
        points_used=points_to_redeem,
        amount_discounted=discount,
    )

    # Write a negative entry to the ledger
    add_ledger_entry(
        db,
        shop_id=shop_id,
        customer_id=customer.id,
        entry_type="redeem",
        points=-points_to_redeem,  # negative because points are going out
        reference_id=redemption.id,
    )
    db.commit()

    return redemption, None
