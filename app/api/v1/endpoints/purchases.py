from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.config.database import get_db
from app.repositories.customer_repo import get_customer_by_contact
from app.services.purchase_service import calculate_points
from app.utils import response_parser
from app.core import messages
from app.core.dependencies import get_current_user
from app.models.purchase import Purchase
from app.repositories.points_ledger_repo import add_ledger_entry
from app.repositories.purchase_repo import get_recent_purchases
from app.schemas.purchase import PurchaseCreate
from app.services.coupon_service import validate_coupon, redeem_coupon
from app.services.notification_service import emit_notification

from app.services.redemption_service import calculate_discount
from app.models.redemption import Redemption
from app.repositories.redemption_repo import create_redemption

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("")
def add_purchase(
    data: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        # 1. Customer Verification
        customer = get_customer_by_contact(db, shop_id=current_user.id, phone=data.phone)
        if not customer:
            raise response_parser.generate_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=messages.CUSTOMER_NOT_FOUND,
                success=False,
            )

        # 2. Points Earnings Calculation (Gross Based)
        earned_points = calculate_points(data.amount)
        
        # 3. Discount Logic Initialization
        coupon_usage_id = None
        redemption_id = None
        coupon_discount = 0
        points_discount = 0
        payable_amount = data.amount
        points_redeemed = data.points_to_redeem

        # 4. Coupon Validation & Stacking Check
        coupon = None
        if data.coupon_code:
            v_res = validate_coupon(db, current_user.id, data.coupon_code)
            if not v_res["valid"]:
                 raise response_parser.generate_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=v_res["message"],
                    success=False
                )
            coupon = v_res["coupon"]
            
            # Enforce Stacking Rules
            if points_redeemed > 0 and not coupon["is_stackable"]:
                raise response_parser.generate_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Coupon '{coupon['code']}' cannot be combined with point redemption.",
                    success=False
                )

        # 5. Point Balance Check
        if points_redeemed > 0:
            if customer.points < points_redeemed:
                raise response_parser.generate_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Insufficient points. Customer has {customer.points} points.",
                    success=False
                )

        # 6. Apply Coupon Discount (Applied First)
        if coupon:
            if coupon["type"] == "percentage":
                coupon_discount = (data.amount * coupon["value"]) // 100
                if coupon["max_discount_cap"] and coupon_discount > coupon["max_discount_cap"]:
                    coupon_discount = int(coupon["max_discount_cap"])
            else:
                coupon_discount = int(coupon["value"])
            
            coupon_discount = min(coupon_discount, data.amount)
            payable_amount -= coupon_discount

        # 7. Apply Points Discount (Applied to remaining balance)
        if points_redeemed > 0:
            points_value = calculate_discount(points_redeemed)
            points_discount = min(points_value, payable_amount)
            payable_amount -= points_discount

        # 8. Order Protocol: Redemption & Usage Records
        # Note: We create these first to get IDs for the Purchase record
        
        if coupon:
            # redeem_coupon utility ensures min_order_value etc are met
            usage_res = redeem_coupon(db, current_user.id, coupon["code"], data.phone, data.amount)
            coupon_usage_id = usage_res["redemption_id"]

        if points_redeemed > 0:
            # Force points discount value to what we calculated (to avoid rounding diffs)
            redemption = create_redemption(
                db,
                shop_id=current_user.id,
                customer_id=customer.id,
                points_used=points_redeemed,
                amount_discounted=points_discount
            )
            db.flush()
            redemption_id = redemption.id
            
            # Deduct points from customer
            customer.points -= points_redeemed
            
            # Ledger for point deduction
            add_ledger_entry(
                db,
                shop_id=current_user.id,
                customer_id=customer.id,
                entry_type="redeem",
                points=-points_redeemed,
                reference_id=redemption_id,
            )

        # 9. Create Main Purchase Audit
        purchase = Purchase(
            shop_id=current_user.id,
            customer_id=customer.id,
            amount=data.amount,
            points_earned=earned_points,
            coupon_code=data.coupon_code,
            coupon_usage_id=coupon_usage_id,
            redemption_id=redemption_id,
            points_redeemed=points_redeemed,
            coupon_discount=coupon_discount,
            points_discount=points_discount,
            payable_amount=payable_amount
        )

        db.add(purchase)
        
        # Add earned points from this transaction
        customer.points += earned_points
        db.flush() 
        
        # Ledger for points earned
        add_ledger_entry(
            db,
            shop_id=current_user.id,
            customer_id=customer.id,
            entry_type="earn",
            points=earned_points,
            reference_id=purchase.id,
        )
        
        db.commit()

        # 10. Fire Notification for meaningful events
        if coupon_discount > 0 or points_discount > 0:
            parts = []
            if coupon_discount > 0:
                parts.append(f"coupon ({data.coupon_code}) saved ₹{coupon_discount}")
            if points_discount > 0:
                parts.append(f"points redeemed saved ₹{points_discount}")
            savings_summary = " & ".join(parts)
            emit_notification(
                db, current_user.id,
                "Transaction Processed",
                f"{customer.name}'s purchase of ₹{data.amount}: {savings_summary}. Net payable: ₹{payable_amount}.",
                "financial"
            )
        else:
            emit_notification(
                db, current_user.id,
                "New Purchase",
                f"{customer.name} made a purchase of ₹{data.amount} and earned {earned_points} points.",
                "system"
            )

        return response_parser.success_response(
            message=messages.PURCHASE_ADDED_SUCCESSFULLY,
            data={
                "earned_points": earned_points, 
                "total_points": customer.points,
                "coupon_discount": coupon_discount,
                "points_discount": points_discount,
                "payable_amount": payable_amount
            },
        )
    except Exception as err:
        db.rollback()
        if hasattr(err, "status_code"):
            raise err
        logger.error(f"Internal Server Error in add_purchase(): {str(err)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )
@router.get("")
def list_purchases(
    page: int = 1,
    size: int = 10,
    date_filter: Optional[str] = Query(default="all"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        data = get_recent_purchases(
            db, shop_id=current_user.id, page=page, size=size, date_filter=date_filter
        )
        return response_parser.success_response(
            message="Recent purchases fetched successfully",
            data=data
        )
    except Exception as err:
        logger.error(f"Internal Server Error in list_purchases(): {str(err)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )
