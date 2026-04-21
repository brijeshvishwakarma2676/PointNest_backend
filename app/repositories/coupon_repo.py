from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.coupon import Coupon, CouponUsage
from typing import Optional, List, Tuple

def create_coupon(db: Session, shop_id: int, data: dict) -> Coupon:
    coupon = Coupon(**data, shop_id=shop_id)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

def get_coupon_by_code(db: Session, shop_id: int, code: str) -> Optional[Coupon]:
    return db.query(Coupon).filter(
        Coupon.shop_id == shop_id,
        Coupon.code == code,
        Coupon.is_active == 1
    ).first()

def get_coupons(
    db: Session, 
    shop_id: int, 
    search_query: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[int, List[Coupon]]:
    query = db.query(Coupon).filter(Coupon.shop_id == shop_id, Coupon.is_active == 1)
    
    if search_query:
        query = query.filter(Coupon.code.ilike(f"%{search_query}%"))
    
    total = query.count()
    items = query.order_by(Coupon.created_at.desc()).offset(skip).limit(limit).all()
    
    return total, items

def get_coupon_by_id(db: Session, shop_id: int, coupon_id: int) -> Optional[Coupon]:
    return db.query(Coupon).filter(
        Coupon.shop_id == shop_id,
        Coupon.id == coupon_id,
        Coupon.is_active == 1
    ).first()

def get_coupon_by_id_with_history(db: Session, shop_id: int, coupon_id: int) -> Optional[Coupon]:
    return db.query(Coupon).options(
        joinedload(Coupon.usages).joinedload(CouponUsage.customer)
    ).filter(
        Coupon.shop_id == shop_id,
        Coupon.id == coupon_id,
        Coupon.is_active == 1
    ).first()

def update_coupon_status(db: Session, coupon: Coupon, status: str) -> Coupon:
    coupon.status = status
    db.commit()
    db.refresh(coupon)
    return coupon

def create_coupon_usage(db: Session, data: dict) -> CouponUsage:
    usage = CouponUsage(**data)
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage

def increment_coupon_usage(db: Session, coupon: Coupon) -> Coupon:
    coupon.usage_count += 1
    db.commit()
    db.refresh(coupon)
    return coupon
