from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class NotificationType(str, Enum):
    system = "system"
    financial = "financial"
    security = "security"
    audit = "audit"

class NotificationCreate(BaseModel):
    title: str
    body: str
    type: NotificationType = NotificationType.system
    is_read: bool = False

class NotificationResponse(BaseModel):
    id: int
    shop_id: int
    title: str
    body: str
    type: str
    is_read: bool
    created_at: datetime
    
    # Optional field that the frontend can use to show an easy '10m ago' reading style
    time: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class NotificationListResponse(BaseModel):
    total: int
    items: List[NotificationResponse]
