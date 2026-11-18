"""Aggregates every v1 endpoint module into one api_router."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, dishes, menu, orders, payments, reviews, stores, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stores.router, tags=["stores"])
api_router.include_router(menu.router, tags=["menu"])
api_router.include_router(dishes.router, tags=["dishes"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(reviews.router, tags=["Reviews"])
