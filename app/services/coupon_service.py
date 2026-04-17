from sqlalchemy.orm import Session
from app.repositories import coupon_repo
from app.schemas.coupon import CouponCreate, CouponResponse
from fastapi import HTTPException, status

def mint_new_coupon(db: Session, shop_id: int, coupon_data: CouponCreate):
    # Check if a coupon with the same code already exists for this shop
    existing = coupon_repo.get_coupon_by_code(db, shop_id, coupon_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coupon protocol '{coupon_data.code}' is already authorized in your registry."
        )
    
    return coupon_repo.create_coupon(db, shop_id, coupon_data.model_dump())

def list_voucher_registry(db: Session, shop_id: int, search_query: str = None, page: int = 1, size: int = 10):
    skip = (page - 1) * size
    total, items = coupon_repo.get_coupons(db, shop_id, search_query, skip, size)
    return {"total": total, "items": items}

def toggle_coupon_authorization(db: Session, shop_id: int, coupon_id: int):
    coupon = coupon_repo.get_coupon_by_id(db, shop_id, coupon_id)
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified voucher protocol not found in this shop's registry."
        )
    
    # Toggle logic
    new_status = "blocked" if coupon.status == "active" else "active"
    return coupon_repo.update_coupon_status(db, coupon, new_status)

def get_coupon_detail(db: Session, shop_id: int, coupon_id: int):
    coupon = coupon_repo.get_coupon_by_id_with_history(db, shop_id, coupon_id)
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher protocol with specified ID not found."
        )
    
    # Format history for frontend
    history = [
        {
            "id": usage.customer.id if usage.customer else "N/A",
            "name": usage.customer.name if usage.customer else "Anonymous Client",
            "used_at": usage.redeemed_at.strftime("%Y-%m-%d %H:%M"),
            "discount": usage.discount_amount
        }
        for usage in coupon.usages
    ]
    
    # Return everything the frontend needs
    return {
        "id": coupon.id,
        "code": coupon.code,
        "type": coupon.type,
        "value": coupon.value,
        "status": coupon.status,
        "start_date": coupon.start_date,
        "expiry_date": coupon.expiry_date,
        "usage_count": coupon.usage_count,
        "max_usage": coupon.max_usage_global,
        "max_usage_per_user": coupon.max_usage_per_user,
        "max_discount_cap": coupon.max_discount_cap,
        "min_order_value": coupon.min_order_value,
        "is_stackable": coupon.is_stackable,
        "eligibility_type": coupon.eligibility_type,
        "created_at": coupon.created_at,
        "history": history[::-1] # Newest usage first
    }
