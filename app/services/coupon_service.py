from sqlalchemy.orm import Session
from app.schemas.coupon import CouponCreate, CouponResponse, CouponValidateResponse
from app.repositories import coupon_repo, customer_repo
from fastapi import HTTPException, status
from app.utils.datetime_utils import get_ist_now

def mint_new_coupon(db: Session, shop_id: int, coupon_data: CouponCreate):
    # Check if a coupon with the same code already exists for this shop
    existing = coupon_repo.get_coupon_by_code(db, shop_id, coupon_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coupon protocol '{coupon_data.code}' is already authorized in your registry."
        )
    
    return coupon_repo.create_coupon(db, shop_id, coupon_data.model_dump())

def list_voucher_registry(db: Session, shop_id: int, search_query: str = None, page: int = 1, size: int = 5):
    skip = (page - 1) * size
    total, items = coupon_repo.get_coupons(db, shop_id, search_query, skip, size)
    
    processed_items = [CouponResponse.model_validate(item).model_dump(mode='json') for item in items]
    return {"total": total, "page": page, "size": size, "items": processed_items}

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
    
    validated = CouponResponse.model_validate(coupon).model_dump(mode='json')
    
    # Return everything the frontend needs
    return {
        "id": coupon.id,
        "code": coupon.code,
        "type": coupon.type,
        "value": coupon.value,
        "status": validated["status"],
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

def validate_coupon(db: Session, shop_id: int, code: str) -> dict:
    coupon = coupon_repo.get_coupon_by_code(db, shop_id, code)
    
    if not coupon:
        return {"valid": False, "message": "Voucher code not found or inactive.", "coupon": None}
    
    # Check expiry
    now = get_ist_now()
    validated_coupon = CouponResponse.model_validate(coupon).model_dump(mode='json')
    if coupon.expiry_date and coupon.expiry_date < now:
        return {"valid": False, "message": f"This coupon was valid until {coupon.expiry_date.strftime('%Y-%m-%d %H:%M')}. It has now expired.", "coupon": validated_coupon}
    
    # Check start date
    if coupon.start_date and coupon.start_date > now:
        return {"valid": False, "message": f"This coupon protocol is not yet active. It will start on {coupon.start_date.strftime('%Y-%m-%d %H:%M')}.", "coupon": validated_coupon}
    
    # Check global usage limits
    if coupon.usage_count >= coupon.max_usage_global:
        return {"valid": False, "message": "This coupon has reached its maximum global usage limit.", "coupon": CouponResponse.model_validate(coupon).model_dump(mode='json')}
    
    return {"valid": True, "message": "Coupon authorized for redemption.", "coupon": CouponResponse.model_validate(coupon).model_dump(mode='json')}

def redeem_coupon(db: Session, shop_id: int, code: str, customer_phone: str, order_amount: float):
    # 1. Validate
    val_result = validate_coupon(db, shop_id, code)
    if not val_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=val_result["message"]
        )
    
    coupon = val_result["coupon"]
    
    # 2. Minimum Order Value Check
    if order_amount < coupon.min_order_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum order value for this coupon is ₹{coupon.min_order_value}. Current amount is ₹{order_amount}."
        )

    # 3. Get Customer
    customer = customer_repo.get_customer_by_contact(db, shop_id, phone=customer_phone)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found. Please register the customer first to redeem coupons."
        )
    
    # 4. Calculate Discount
    discount_amount = 0.0
    if coupon.type == "percentage":
        discount_amount = order_amount * (coupon.value / 100)
        if coupon.max_discount_cap:
            discount_amount = min(discount_amount, coupon.max_discount_cap)
    else: # fixed
        discount_amount = min(coupon.value, order_amount) # Can't discount more than the order itself
    
    # 5. Record Usage
    usage_data = {
        "coupon_id": coupon.id,
        "customer_id": customer.id,
        "discount_amount": discount_amount,
        "redeemed_at": get_ist_now()
    }
    
    usage_record = coupon_repo.create_coupon_usage(db, usage_data)
    
    # 6. Increment Usage Count
    coupon_repo.increment_coupon_usage(db, coupon)
    
    return {
        "success": True,
        "coupon_code": coupon.code,
        "discount_applied": discount_amount,
        "customer_name": customer.name,
        "redemption_id": usage_record.id
    }
