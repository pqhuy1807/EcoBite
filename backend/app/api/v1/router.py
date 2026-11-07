"""Aggregates every v1 endpoint module into one api_router.

New modules (items, dishes, orders, ...) follow the same pattern:
    from app.api.v1.endpoints import items
    api_router.include_router(items.router, prefix="/items", tags=["items"])
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, dishes, menu, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(menu.router, tags=["menu"])
api_router.include_router(dishes.router, tags=["dishes"])
