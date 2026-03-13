from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, customers, points, purchases, redemptions

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(customers.router)
api_router.include_router(points.router)
api_router.include_router(purchases.router)
api_router.include_router(redemptions.router)
