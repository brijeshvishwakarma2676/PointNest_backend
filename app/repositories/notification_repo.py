from sqlalchemy.orm import Session
from app.models.notification import Notification
from typing import List, Tuple

def create_notification(db: Session, shop_id: int, data: dict) -> Notification:
    notification = Notification(**data, shop_id=shop_id)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def get_notifications(db: Session, shop_id: int, limit: int = 20) -> Tuple[int, List[Notification]]:
    query = db.query(Notification).filter(Notification.shop_id == shop_id)
    total = query.count()
    items = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return total, items

def get_unread_count(db: Session, shop_id: int) -> int:
    return db.query(Notification).filter(
        Notification.shop_id == shop_id,
        Notification.is_read == False
    ).count()

def mark_as_read(db: Session, shop_id: int, notification_id: int) -> Notification:
    notification = db.query(Notification).filter(
        Notification.shop_id == shop_id,
        Notification.id == notification_id
    ).first()
    
    if notification:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
    return notification

def mark_all_as_read(db: Session, shop_id: int):
    val = db.query(Notification).filter(
        Notification.shop_id == shop_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return val

def delete_all_notifications(db: Session, shop_id: int):
    val = db.query(Notification).filter(Notification.shop_id == shop_id).delete()
    db.commit()
    return val
