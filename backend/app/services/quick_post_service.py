"""Gemini Quick-Post service (PA5 head-start).

Extracts surplus-dish listings from free-text input via Google Gemini 2.5 Flash
with Pydantic Structured Output, then applies the Allergen Hard Filter
(Guardrail #7) before returning results to the caller.

The Gemini client is injected (optional) so the service can be unit-tested with
a fake client and degrades gracefully when the LLM is unavailable or returns
malformed output — the app never crashes because of Quick-Post.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any, Protocol, runtime_checkable
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import google.genai
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.nlp import QuickPostExtractionResponse

logger = logging.getLogger(__name__)

# Exception Domain


class QuickPostInputError(ValueError):
    def __init__(self, message: str, *, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


class QuickPostUnavailableError(RuntimeError):
    pass


class QuickPostStoreNotFoundError(LookupError):
    pass


class QuickPostStoreNotApprovedError(PermissionError):
    pass


@runtime_checkable
class GeminiQuickPostClient(Protocol):
    """Duck-typed Gemini client — only `generate_content` is required."""

    async def generate_content(
        self,
        *,
        model: str,
        contents: Any,
        config: Any,
    ) -> Any:  # pragma: no cover - protocol stub
        """Generate content and return an object with `.parsed` (Pydantic model)."""
        ...


class GoogleGenAIQuickPostAdapter:
    """Async adapter wrapping google-genai with a bounded timeout."""

    def __init__(self, api_key: str, timeout_seconds: int | None = None) -> None:
        self._client = google.genai.Client(api_key=api_key)
        self._timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else settings.GEMINI_TIMEOUT_SECONDS
        )

    async def generate_content(self, *, model: str, contents: Any, config: Any) -> Any:
        """Generate content asynchronously without blocking the FastAPI event loop."""
        return await asyncio.wait_for(
            self._client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            ),
            timeout=self._timeout_seconds,
        )


MAX_PROMPT_MENU_ITEMS = 50
VN_TZ: tzinfo
try:
    VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except ZoneInfoNotFoundError:
    VN_TZ = timezone(timedelta(hours=7))


class QuickPostService:
    """AI Feature 1 service — Batch Quick-Post Multimodal Assistant (WIP)."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        gemini_client: GeminiQuickPostClient | None = None,
    ) -> None:
        self.db = db
        self.gemini_client = gemini_client

    async def parse_dish_nlp(
        self,
        *,
        owner_id: UUID,
        raw_text: str | None = None,
        audio_bytes: bytes | None = None,
        audio_mime_type: str | None = None,
        audio_filename: str | None = None,
        reference_time: datetime | None = None,
    ) -> QuickPostExtractionResponse:
        """Extract surplus dishes via Gemini 2.5 Flash (WIP — Chặng 1–4)."""
        raise NotImplementedError("QuickPostService.parse_dish_nlp is in progress")


def build_quick_post_service(
    db: AsyncSession,
    gemini_client: GeminiQuickPostClient | None = None,
) -> QuickPostService:
    """Factory for ``QuickPostService`` — keeps endpoint layer dependency-free."""
    if gemini_client is not None:
        return QuickPostService(db, gemini_client=gemini_client)

    try:
        resolved_client: GeminiQuickPostClient | None = GoogleGenAIQuickPostAdapter(
            api_key=settings.gemini_key,
            timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
        )
    except ValueError:
        logger.warning("Quick-Post: Gemini API key not configured — running in degraded mode")
        resolved_client = None
    return QuickPostService(db, gemini_client=resolved_client)
