from fastapi import APIRouter, Depends, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
import logging

from app.config.database import get_db
from app.schemas.customer import CustomerCreate
from app.repositories.customer_repo import create_customer
from app.utils import response_parser
from app.core import messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("")
def add_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    try:
        customer = create_customer(db, data.model_dump())
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
    except Exception as err:
        if hasattr(err, "status_code"):
            raise err
        logger.exception(f"Some Error Occurred in add_customer(): {err}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )
