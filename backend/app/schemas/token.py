"""Pydantic schemas for authentication tokens."""

from pydantic import BaseModel


class UserLoginData(BaseModel):
    """Essential user details returned upon successful login."""

    id: str
    email: str
    full_name: str
    role: str
    green_points_balance: int = 0
    created_at: str | None = None


class LoginRequest(BaseModel):
    """Credentials payload for JSON-based login."""

    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Payload to exchange a refresh token for a new access token."""

    refresh_token: str


class Token(BaseModel):
    """OAuth2-compatible dual-token authentication response."""

    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None
    expires_in: int | None = None
    user: UserLoginData | None = None


class TokenPayload(BaseModel):
    """Decoded JWT claims relevant to authentication."""

    sub: str | None = None
    exp: int | None = None
    type: str | None = None
