"""Pydantic schemas for authentication tokens."""

from pydantic import BaseModel


class Token(BaseModel):
    """OAuth2-compatible bearer token response."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT claims relevant to authentication."""

    sub: str | None = None
    exp: int | None = None
