"""Public interface for the output interception and real-time stream rendering module."""

from .interceptor import OutputInterceptor  # type: ignore[import-not-found]

# PUBLIC EXPORTS: STABLE PACKAGE API SURFACE
# Exposes the primary stream output interceptor class for filtering and rewriting console streams.
__all__ = [
    "OutputInterceptor",
]
