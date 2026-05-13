from sqlalchemy.orm import Session
from app.repositories import notification_repo
from app.schemas.notification import NotificationCreate, NotificationType, NotificationResponse
from app.utils.datetime_utils import get_ist_now
from typing import List

def _format_time_ago(dt) -> str:
    now = get_ist_now()
    diff = now - dt
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"

def emit_notification(db: Session, shop_id: int, title: str, body: str, type: str = "system"):
    """Helper method accessible globally to mint a notification quietly."""
    data = NotificationCreate(
        title=title,
        body=body,
        type=NotificationType(type)
    ).model_dump()
    return notification_repo.create_notification(db, shop_id, data)

def list_shop_notifications(db: Session, shop_id: int, limit: int = 20):
    total, items = notification_repo.get_notifications(db, shop_id, limit)
    unread_count = notification_repo.get_unread_count(db, shop_id)
    
    # Process Pydantic validation & add relative time string
    processed = []
    for item in items:
        as_dict = NotificationResponse.model_validate(item).model_dump()
        as_dict["time"] = _format_time_ago(item.created_at)
        processed.append(as_dict)
        
    return {"total": total, "unread_count": unread_count, "items": processed}

def mark_notification_read(db: Session, shop_id: int, notif_id: int):
    return notification_repo.mark_as_read(db, shop_id, notif_id)

def mark_all_read(db: Session, shop_id: int):
    return notification_repo.mark_all_as_read(db, shop_id)

def clear_all(db: Session, shop_id: int):
    return notification_repo.delete_all_notifications(db, shop_id)
