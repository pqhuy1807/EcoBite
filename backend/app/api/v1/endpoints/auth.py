"""Auth module endpoints: registration, hybrid login (JSON/Form), and token refresh."""

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import DBSession
from app.models.user import User
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserResponse
from app.services import auth as auth_service
from app.services import user as user_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def register(user_in: UserCreate, db: DBSession) -> User:
    """Create a consumer/store-partner account; duplicate emails return 409."""
    if await user_service.get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    return await user_service.create_user(db, user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="User login (supports JSON {email, password} and OAuth2 Form data)",
)
async def login(
    request: Request,
    db: DBSession,
) -> Token:
    """Exchange credentials for bearer access & refresh tokens."""
    content_type = request.headers.get("content-type", "")
    email: str | None = None
    password: str | None = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                email = body.get("email") or body.get("username")
                password = body.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid JSON payload",
            ) from None
    else:
        form = await request.form()
        raw_email = form.get("username") or form.get("email")
        raw_pw = form.get("password")
        email = str(raw_email) if raw_email is not None else None
        password = str(raw_pw) if raw_pw is not None else None

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Missing email or password",
        )

    token = await auth_service.login_for_user(db, email, password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token using refresh token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: DBSession,
) -> Token:
    """Exchange a valid refresh token for a fresh token pair."""
    token = await auth_service.refresh_user_token(db, payload.refresh_token)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token
