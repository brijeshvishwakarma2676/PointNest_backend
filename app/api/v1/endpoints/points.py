from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import logging

from app.config.database import get_db
from app.repositories.customer_repo import get_customer_by_contact
from app.utils import response_parser
from app.core import messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/points", tags=["points"])


@router.get("")
def check_points(
    phone: str | None = None, email: str | None = None, db: Session = Depends(get_db)
):
    try:
        if not phone and not email:
            raise response_parser.generate_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Phone or email required",  # Dynamic msg or constant
                success=False,
            )

        customer = get_customer_by_contact(db, phone, email)

        if not customer:
            raise response_parser.generate_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=messages.CUSTOMER_NOT_FOUND,
                success=False,
            )

        return response_parser.success_response(
            message=messages.POINTS_RETRIEVED_SUCCESSFULLY,
            data={"name": customer.name, "points": customer.points},
        )
    except Exception as err:
        if hasattr(err, "status_code"):
            raise err
        logger.exception(f"Some Error Occurred in check_points(): {err}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )
