from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "shop_name": current_user.shop_name,
        "email": current_user.email,
        "phone": current_user.phone
    }