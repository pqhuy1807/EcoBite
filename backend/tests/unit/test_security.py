"""Unit tests for core/security.py (password hashing + JWT encode/decode)."""

from datetime import timedelta

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_returns_bcrypt_hash(self) -> None:
        hashed = hash_password("S3curePass!2024")

        assert hashed.startswith("$2b$")
        assert hashed != "S3curePass!2024"

    def test_verify_password_accepts_correct_plain(self) -> None:
        hashed = hash_password("S3curePass!2024")

        assert verify_password("S3curePass!2024", hashed) is True

    def test_verify_password_rejects_wrong_plain(self) -> None:
        hashed = hash_password("S3curePass!2024")

        assert verify_password("WrongPass", hashed) is False


class TestJwtTokens:
    def test_token_roundtrip_keeps_subject(self) -> None:
        token = create_access_token(subject="42")

        payload = decode_access_token(token)
        assert payload["sub"] == "42"
        assert payload["exp"] > payload["iat"]

    def test_expired_token_is_rejected(self) -> None:
        # Token already expired at creation time -> must fail decode (JWTError).
        token = create_access_token(subject="42", expires_delta=timedelta(seconds=-60))

        with pytest.raises(JWTError):
            decode_access_token(token)
