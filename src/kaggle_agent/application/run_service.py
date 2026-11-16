"""Run lifecycle helpers, exit codes, and structured logging."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

EXIT_OK = 0
EXIT_VALIDATION_ERROR = 2
EXIT_RUN_FAILURE = 3
EXIT_BUDGET_VIOLATION = 4


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.dev.ConsoleRenderer(),
        ]
    )


def new_run_id() -> str:
    return str(uuid.uuid4())


def new_entry_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
