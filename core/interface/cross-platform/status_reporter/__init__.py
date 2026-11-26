"""Public interface for the status reporting and structured logging library."""

from .core import report_status  # type: ignore[import-not-found]
from .models import LogContext  # type: ignore[import-not-found]
from .constants import StatusState, LogFormat, LogSeverity  # type: ignore[import-not-found]

# PUBLIC EXPORTS: STABLE PACKAGE API SURFACE
# Exposes the primary entry point, context container, and typing aliases.
__all__ = [
    "report_status",
    "LogContext",
    "StatusState",
    "LogFormat",
    "LogSeverity",
]
