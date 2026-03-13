from app.models.points_ledger import PointsLedger


def add_ledger_entry(
    db,
    shop_id: int,
    customer_id: int,
    entry_type: str,
    points: int,
    reference_id: int = None,
):
    """
    Add a single entry to the points ledger.
    entry_type: "earn" or "redeem"
    points    : positive for earn, negative for redeem
    """
    entry = PointsLedger(
        shop_id=shop_id,
        customer_id=customer_id,
        type=entry_type,
        points=points,
        reference_id=reference_id,
    )
    db.add(entry)
    # Flush without commit so the caller controls the transaction
    db.flush()
    return entry


def get_ledger_by_customer(
    db, shop_id: int, customer_id: int, skip: int = 0, limit: int = 20
):
    total = (
        db.query(PointsLedger)
        .filter(
            PointsLedger.shop_id == shop_id,
            PointsLedger.customer_id == customer_id,
            PointsLedger.is_active == 1,
        )
        .count()
    )
    entries = (
        db.query(PointsLedger)
        .filter(
            PointsLedger.shop_id == shop_id,
            PointsLedger.customer_id == customer_id,
            PointsLedger.is_active == 1,
        )
        .order_by(PointsLedger.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return total, entries
