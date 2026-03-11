from fastapi import APIRouter, Depends, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.config.database import get_db
from app.schemas.customer import CustomerCreate, CustomerListRequest
from app.repositories.customer_repo import create_customer, get_customers, get_customer_by_id
from app.utils import response_parser
from app.core import messages
from app.core.dependencies import get_current_user
from app.services.customer_service import get_or_create_customer

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


@router.post("/find-or-create")
def find_or_create(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        customer_data = data.model_dump()
        customer_data["shop_id"] = current_user.id

        customer, is_new = get_or_create_customer(db, current_user.id, customer_data)

        return response_parser.success_response(
            message=messages.CUSTOMER_RETRIEVED_OR_CREATED_SUCCESSFULLY,
            data={
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "points": customer.points,
                "is_new_customer": is_new,
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
        logger.error(f"Internal Server Error in find_or_create(): {str(err)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )


@router.post("/list")
def list_customers(
    data: CustomerListRequest | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if data is None:
        data = CustomerListRequest()
    try:
        skip = (data.page - 1) * data.size
        total, customers = get_customers(
            db, current_user.id, data.search_query, skip, data.size
        )

        return response_parser.success_response(
            message=messages.CUSTOMERS_FETCHED_SUCCESSFULLY,
            data={
                "items": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "phone": c.phone,
                        "email": c.email,
                        "points": c.points,
                    }
                    for c in customers
                ],
                "total": total,
                "page": data.page,
                "size": data.size,
                "total_pages": (
                    (total + data.size - 1) // data.size if data.size > 0 else 0
                ),
            },
        )
    except Exception as err:
        if hasattr(err, "status_code"):
            raise err
        logger.error(f"Internal Server Error in list_customers(): {str(err)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )


@router.get("/get_details")
def get_customer_details(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        customer = get_customer_by_id(db, current_user.id, customer_id)
        if not customer:
            raise response_parser.generate_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=messages.CUSTOMER_NOT_FOUND,
                success=False,
            )
        return response_parser.success_response(
            message=messages.CUSTOMER_FETCHED_SUCCESSFULLY,
            data={
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "points": customer.points,
            },
        )
    except Exception as err:
        if hasattr(err, "status_code"):
            raise err
        logger.error(f"Internal Server Error in get_customer_details(): {str(err)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )
