"""Unit tests for Gemini dual-key configuration in Settings (TDD — Phase 1 T002)."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

GEMINI_ENV_VARS = (
    "GEMINI_DEMO_API",
    "GEMINI_TEST_API",
    "GEMINI_MODEL",
    "GEMINI_TIMEOUT_SECONDS",
    "GEMINI_USE_DEMO_KEY",
)


@pytest.fixture(autouse=True)
def _clean_gemini_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from host environment variables and never read backend/.env."""
    for var in GEMINI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def _make_settings(**overrides: object) -> Settings:
    """Build Settings without loading the local .env file."""
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


class TestGeminiSettings:
    def test_defaults_to_test_key_and_gemini_25_flash(self) -> None:
        cfg = _make_settings(
            GEMINI_TEST_API="free-test-key",
            GEMINI_DEMO_API="paid-demo-key",
        )

        assert cfg.GEMINI_USE_DEMO_KEY is False
        assert cfg.GEMINI_MODEL == "gemini-2.5-flash"
        assert cfg.GEMINI_TIMEOUT_SECONDS == 15
        assert cfg.gemini_key == "free-test-key"

    def test_uses_demo_key_only_when_flag_enabled(self) -> None:
        cfg = _make_settings(
            GEMINI_TEST_API="free-test-key",
            GEMINI_DEMO_API="paid-demo-key",
            GEMINI_USE_DEMO_KEY=True,
        )

        assert cfg.gemini_key == "paid-demo-key"

    def test_gemini_key_strips_surrounding_whitespace(self) -> None:
        cfg = _make_settings(GEMINI_TEST_API="  free-test-key-with-spaces \n")

        assert cfg.gemini_key == "free-test-key-with-spaces"

    @pytest.mark.parametrize("use_demo_key", [False, True])
    @pytest.mark.parametrize("raw_key", ["", "   ", "\t\n"])
    def test_missing_or_blank_gemini_key_raises_value_error(
        self,
        use_demo_key: bool,
        raw_key: str,
    ) -> None:
        cfg = _make_settings(
            GEMINI_TEST_API=raw_key,
            GEMINI_DEMO_API=raw_key,
            GEMINI_USE_DEMO_KEY=use_demo_key,
        )

        with pytest.raises(ValueError, match="Gemini API key"):
            _ = cfg.gemini_key

    def test_settings_can_boot_without_gemini_keys_configured(self) -> None:
        """Missing Gemini keys must not break app startup or unrelated unit tests."""
        cfg = _make_settings()

        assert cfg.GEMINI_TEST_API == ""
        assert cfg.GEMINI_DEMO_API == ""

    @pytest.mark.parametrize("invalid_timeout", [0, -1, -15])
    def test_gemini_timeout_must_be_strictly_positive(self, invalid_timeout: int) -> None:
        with pytest.raises(ValidationError):
            _make_settings(GEMINI_TIMEOUT_SECONDS=invalid_timeout)
