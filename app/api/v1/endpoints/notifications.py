from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Optional

from app.config.database import get_db
from app.core.dependencies import get_current_user
from app.utils import response_parser
from app.core import messages
from app.services.notification_service import (
    list_shop_notifications,
    mark_notification_read,
    mark_all_read,
    clear_all
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=None)
def get_recent_notifications(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        data = list_shop_notifications(db, current_user.id, limit)
        return response_parser.success_response(
            message="Notifications fetched successfully",
            data=data
        )
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False
        )

@router.patch("/{notif_id}/read")
def read_notification(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        mark_notification_read(db, current_user.id, notif_id)
        return response_parser.success_response(message="Alert marked as read")
    except Exception as e:
        logger.error(f"Error in read_notification: {str(e)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False
        )

@router.patch("/read-all")
def read_all_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        mark_all_read(db, current_user.id)
        return response_parser.success_response(message="All alerts marked read")
    except Exception as e:
        logger.error(f"Error in read_all_notifications: {str(e)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False
        )

@router.delete("/clear-all")
def clear_all_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        clear_all(db, current_user.id)
        return response_parser.success_response(message="Notification ledger cleared")
    except Exception as e:
        logger.error(f"Error in clear_all_notifications: {str(e)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=messages.INTERNAL_SERVER_ERROR,
            success=False
        )
