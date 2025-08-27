"""Middleware and filters for the FastAPI application."""

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class ExcludeEndpointFilter(logging.Filter):
    """Filter to exclude specific endpoint logs from being logged."""

    def __init__(self, exclude_patterns: Optional[list[str]] = None):
        super().__init__()
        self.exclude_patterns = exclude_patterns or ["/metrics", "?streaming=true"]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out records containing excluded patterns.

        Args:
            record: The log record to filter

        Returns:
            bool: True if the record should be logged, False otherwise
        """
        message = record.getMessage()
        return not any(pattern in message for pattern in self.exclude_patterns)


def setup_cors(app: FastAPI, allow_origins: list[str] = None) -> None:
    """Setup CORS middleware for the application.

    Args:
        app: The FastAPI application instance
        allow_origins: List of allowed origins. Defaults to ["*"]
    """
    origins = allow_origins or ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_logging_filters() -> None:
    """Configure logging filters for uvicorn access logs."""
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.addFilter(ExcludeEndpointFilter())
