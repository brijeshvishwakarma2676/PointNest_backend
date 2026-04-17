from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Optional

from app.config.database import get_db
from app.core.dependencies import get_current_user
from app.utils import response_parser
from app.core import messages
from app.schemas.coupon import CouponCreate, CouponListResponse
from app.services.coupon_service import (
    mint_new_coupon,
    list_voucher_registry,
    toggle_coupon_authorization
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coupons", tags=["coupons"])

@router.post("")
def mint_coupon(
    data: CouponCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        coupon = mint_new_coupon(db, current_user.id, data)
        return response_parser.success_response(
            message=messages.COUPON_MINTED_SUCCESSFULLY,
            data=coupon
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error in mint_coupon(): {str(e)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False
        )

@router.get("", response_model=None)
def get_coupon_registry(
    search_query: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        registry = list_voucher_registry(db, current_user.id, search_query, page, size)
        return response_parser.success_response(
            message=messages.COUPONS_FETCHED_SUCCESSFULLY,
            data=registry
        )
    except Exception as e:
        logger.error(f"Internal Server Error in get_coupon_registry(): {str(e)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False
        )

@router.patch("/{coupon_id}/status")
def update_coupon_status(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        coupon = toggle_coupon_authorization(db, current_user.id, coupon_id)
        return response_parser.success_response(
            message=messages.COUPON_STATUS_UPDATED_SUCCESSFULLY,
            data=coupon
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error in update_coupon_status(): {str(e)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False
        )

@router.get("/{coupon_id}")
def get_vouchers_audit_detail(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        from app.services.coupon_service import get_coupon_detail
        detail = get_coupon_detail(db, current_user.id, coupon_id)
        return response_parser.success_response(
            message=messages.COUPONS_FETCHED_SUCCESSFULLY,
            data=detail
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Internal Server Error in get_vouchers_audit_detail(): {str(e)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False
        )
