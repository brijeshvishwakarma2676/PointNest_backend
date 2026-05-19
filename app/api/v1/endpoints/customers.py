from fastapi import APIRouter, Depends, status, BackgroundTasks
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
import logging

from app.config.database import get_db
from app.schemas.customer import CustomerCreate, CustomerListRequest, CustomerUpdate
from app.repositories.customer_repo import (
    create_customer,
    get_customers,
    get_customer_by_id,
    get_customer_by_contact,
)
from app.repositories.points_ledger_repo import get_ledger_by_customer
from app.utils import response_parser
from app.core import messages
from app.core.dependencies import get_current_user
from app.services.customer_service import get_or_create_customer, update_customer
from app.services.email_service import send_welcome_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("")
def add_customer(
    data: CustomerCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        customer_data = data.model_dump()
        customer_data["shop_id"] = current_user.id

        customer = create_customer(db, customer_data)
        
        # Outbound welcome email dispatch (non-blocking)
        if customer.email:
            send_welcome_email(
                background_tasks=background_tasks,
                recipient_email=customer.email,
                customer_name=customer.name,
                initial_points=customer.points
            )

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        customer_data = data.model_dump()
        customer_data["shop_id"] = current_user.id

        customer, is_new = get_or_create_customer(db, current_user.id, customer_data)

        # Outbound welcome email dispatch if the customer is brand new (non-blocking)
        if is_new and customer.email:
            send_welcome_email(
                background_tasks=background_tasks,
                recipient_email=customer.email,
                customer_name=customer.name,
                initial_points=customer.points
            )

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


@router.put("/update")
def update_customer_endpoint(
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        # exclude_unset=True ensures we only pass fields the user actually provided
        customer_data = data.model_dump(exclude_unset=True)

        customer = update_customer(db, current_user.id, customer_data)

        if not customer:
            raise response_parser.generate_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=messages.CUSTOMER_NOT_FOUND,
                success=False,
            )

        return response_parser.success_response(
            message=messages.CUSTOMER_UPDATED_SUCCESSFULLY,
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
        db.rollback()
        if hasattr(err, "status_code"):
            raise err
        logger.error(f"Internal Server Error in update_customer_endpoint(): {str(err)}")
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


@router.get("/get-details")
def get_customer_details(
    customer_id: Optional[int] = None,
    phone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        customer = None
        if customer_id:
            customer = get_customer_by_id(db, current_user.id, customer_id)
        elif phone:
            customer = get_customer_by_contact(db, current_user.id, phone=phone)

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
                "created_at": customer.created_at,
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


@router.get("/ledger")
def get_customer_ledger(
    customer_id: int,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        skip = (page - 1) * size
        total, entries = get_ledger_by_customer(
            db, current_user.id, customer_id, skip, size
        )

        return response_parser.success_response(
            message=messages.CUSTOMER_FETCHED_SUCCESSFULLY,
            data={
                "items": [
                    {
                        "id": e.id,
                        "type": e.type,
                        "points": e.points,
                        "reference_id": e.reference_id,
                        "created_at": e.created_at,
                    }
                    for e in entries
                ],
                "total": total,
                "page": page,
                "size": size,
                "total_pages": (total + size - 1) // size if size > 0 else 0,
            },
        )
    except Exception as err:
        if hasattr(err, "status_code"):
            raise err
        logger.error(f"Internal Server Error in get_customer_ledger(): {str(err)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False,
        )
