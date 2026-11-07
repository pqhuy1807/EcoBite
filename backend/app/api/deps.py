"""Shared FastAPI dependencies: DB session, current user, role gating."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.dish import Dish
from app.models.menu_item import MenuItem
from app.models.store import Store
from app.models.user import User, UserRole
from app.services import user as user_service

# tokenUrl points at the login form so OpenAPI "Authorize" works out of the box.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Reusable annotated aliases - keeps endpoints clean of bare Depends() calls.
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DBSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Resolve the User from a Bearer JWT (`sub` = user id)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_access_token(token)
        raw_subject = payload.get("sub")
    except JWTError:
        raise credentials_exception from None
    if raw_subject is None:
        raise credentials_exception
    try:
        user_id = uuid.UUID(raw_subject)
    except ValueError:
        raise credentials_exception from None

    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


# Resolvable only after get_current_user is defined (Annotated evaluates eagerly).
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole):
    """Build a dependency that only lets whitelisted roles through.

    Usage (AGENTS.md guardrail #2):
        @router.get("/admin", dependencies=[Depends(require_roles(UserRole.ADMIN))])
    """

    async def role_checker(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have the required role",
            )
        return current_user

    return role_checker


async def require_store_owner(
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> User:
    """Require a store-partner account that owns the store addressed by this route."""
    if current_user.role != UserRole.STORE_PARTNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have the required role",
        )

    raw_store_id = request.path_params.get("store_id")
    if raw_store_id is None:
        raw_entity_id = request.path_params.get("item_id") or request.path_params.get("dish_id")
        is_menu_item = request.path_params.get("item_id") is not None
        if (
            raw_entity_id is None
            and request.method == "POST"
            and (request.url.path.endswith("/dishes") or request.url.path.endswith("/dishes/batch"))
        ):
            payload = await request.json()
            if isinstance(payload, dict) and request.url.path.endswith("/dishes/batch"):
                items = payload.get("dishes")
                raw_entity_id = (
                    items[0].get("menu_item_id")
                    if isinstance(items, list) and items and isinstance(items[0], dict)
                    else None
                )
            else:
                raw_entity_id = payload.get("menu_item_id") if isinstance(payload, dict) else None
            is_menu_item = True
        try:
            entity_id = uuid.UUID(str(raw_entity_id))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store resource not found",
            ) from None

        entity: MenuItem | Dish | None
        if is_menu_item:
            entity = await db.get(MenuItem, entity_id)
        else:
            entity = await db.get(Dish, entity_id)
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store resource not found",
            )
        store_id = entity.store_id
    else:
        try:
            store_id = uuid.UUID(str(raw_store_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found",
            ) from None

    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    if store.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not own this store",
        )
    return current_user


StoreOwner = Annotated[User, Depends(require_store_owner)]
