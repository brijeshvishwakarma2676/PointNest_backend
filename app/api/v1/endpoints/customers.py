from fastapi import APIRouter, Depends, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.config.database import get_db
from app.schemas.customer import CustomerCreate
from app.repositories.customer_repo import create_customer
from app.utils import response_parser
from app.core import messages
from app.core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("")
def add_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        customer_data = data.model_dump()
        customer_data["shop_id"] = current_user.id

        customer = create_customer(db, customer_data)
        return response_parser.success_response(
            message=messages.CUSTOMER_CREATED_SUCCESSFULLY,
            data={
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "points": customer.points,
            },
        )
    except ValidationError as err:
        raise response_parser.generate_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=messages.VALIDATION_ERROR,
            data=err.errors(),
            success=False,
        )
    except IntegrityError:
        db.rollback()
        raise response_parser.generate_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=messages.CUSTOMER_ALREADY_EXISTS,
            success=False,
        )
    except Exception as err:
        db.rollback()
        if hasattr(err, "status_code"):
            raise err
        logger.error(f"Internal Server Error in add_customer(): {str(err)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )
