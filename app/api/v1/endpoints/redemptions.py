from fastapi import APIRouter, Depends, status, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.config.database import get_db
from app.schemas.redemption import RedeemRequest, RedemptionResponse
from app.repositories.customer_repo import get_customer_by_contact
from app.repositories.redemption_repo import get_redemptions_by_shop
from app.services.redemption_service import redeem_points
from app.utils import response_parser
from app.core import messages
from app.core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/redemptions", tags=["redemptions"])


@router.get("")
def get_redemptions(
    page: int = 1,
    size: int = 20,
    date_filter: Optional[str] = Query(default="all"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch recent redemptions for the current shop."""
    try:
        data = get_redemptions_by_shop(
            db, shop_id=current_user.id, page=page, size=size, date_filter=date_filter
        )
        return response_parser.success_response(
            message="Redemptions fetched successfully", data=data
        )
    except Exception as err:
        logger.error(f"Error in get_redemptions(): {str(err)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )


@router.post("/redeem")
def redeem(
    data: RedeemRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        # 1. Find customer by phone under this shop
        customer = get_customer_by_contact(
            db, shop_id=current_user.id, phone=data.phone
        )

        if not customer:
            raise response_parser.generate_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=messages.CUSTOMER_NOT_FOUND,
                success=False,
            )

        # 2. Attempt redemption via service
        redemption, error = redeem_points(
            db,
            customer=customer,
            points_to_redeem=data.points_to_redeem,
            shop_id=current_user.id,
        )

        if error:
            raise response_parser.generate_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=error,
                success=False,
            )

        # 3. Return success
        return response_parser.success_response(
            message=messages.POINTS_REDEEMED_SUCCESSFULLY,
            data={
                "customer_name": customer.name,
                "points_used": redemption.points_used,
                "amount_discounted": redemption.amount_discounted,
                "remaining_points": customer.points,
            },
        )

    except ValidationError as err:
        raise response_parser.generate_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=messages.VALIDATION_ERROR,
            data=err.errors(),
            success=False,
        )
    except Exception as err:
        db.rollback()
        if hasattr(err, "status_code"):
            raise err
        logger.error(f"Internal Server Error in redeem(): {str(err)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )
