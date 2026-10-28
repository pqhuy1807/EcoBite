"""Application entry point.

`app.main:app` builds the FastAPI application: CORS middleware, global
exception handlers, health probe and the bundled API v1 routers.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start/stop heavy singletons exactly once - never inside request bodies.

    Example (per AGENTS.md guardrail #8 - Decoupled ML):

        import torch
        app.state.ml_model = torch.load("best.pt", map_location="cpu")
        yield
        del app.state.ml_model
    """
    logger.info(
        "Starting %s (env=%s, debug=%s)",
        settings.PROJECT_NAME,
        settings.APP_ENV,
        settings.DEBUG,
    )
    yield
    logger.info("Shutdown complete")


def _register_exception_handlers(app: FastAPI) -> None:
    """Global handlers producing predictable JSON error envelopes."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Validation error on %s %s", request.method, request.url.path)
        safe_errors = [
            {"loc": error.get("loc"), "msg": error.get("msg"), "type": error.get("type")}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": safe_errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Full traceback stays in the log; the client only sees a generic 500.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


def create_app() -> FastAPI:
    """Application factory."""
    configure_logging(level=logging.DEBUG if settings.DEBUG else logging.INFO)

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(app)

    @app.get("/health", tags=["Health"], summary="Liveness probe")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


app = create_app()
