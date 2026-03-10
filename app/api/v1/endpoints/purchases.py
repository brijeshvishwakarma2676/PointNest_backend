from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import logging

from app.config.database import get_db
from app.repositories.customer_repo import get_customer_by_contact
from app.services.purchase_service import calculate_points
from app.utils import response_parser
from app.core import messages
from app.core.dependencies import get_current_user
from app.models.purchase import Purchase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("")
def add_purchase(
    phone: str,
    amount: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        customer = get_customer_by_contact(db, shop_id=current_user.id, phone=phone)

        if not customer:
            raise response_parser.generate_response(
                status_code=status.HTTP_404_NOT_NOT_FOUND,
                message=messages.CUSTOMER_NOT_FOUND,
                success=False,
            )

        points = calculate_points(amount)

        purchase = Purchase(
            shop_id=current_user.id,
            customer_id=customer.id,
            amount=amount,
            points_earned=points,
        )

        db.add(purchase)
        customer.points += points
        db.commit()

        return response_parser.success_response(
            message=messages.PURCHASE_ADDED_SUCCESSFULLY,
            data={"earned_points": points, "total_points": customer.points},
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
