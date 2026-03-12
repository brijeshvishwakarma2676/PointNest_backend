from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.core.dependencies import get_current_user
from app.repositories.user_repo import get_shop_metrics

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_me(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    metrics = get_shop_metrics(db, current_user.id)

    return {
        "id": current_user.id,
        "shop_name": current_user.shop_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "metrics": metrics,
    }
