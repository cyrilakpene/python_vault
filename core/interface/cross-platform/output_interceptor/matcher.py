import re
from typing import Any, Callable

from .formatter import format_match  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: LINE INTERCEPTION & REGEX TRANSFORMATION
# This utility evaluates text lines against compiled regex patterns, extracts matched groups,
# applies dynamic formatting or callable transformations, and handles exceptions with safe fallbacks.
# [>] EXECUTING LINE INTERCEPTION
def intercept_line(
    line: str, pattern: re.Pattern[str], target: str | Callable[..., str]
) -> tuple[str, dict[str, Any]]:
    """
    Evaluates text lines against compiled regex patterns and applies dynamic transformations,
    returning both the formatted line and extracted named match groups.

    Args:
        line (str): The raw text line to evaluate and intercept.
        pattern (re.Pattern[str]): The compiled regular expression pattern to search against the line.
        target (str | Callable[..., str]): The formatting string template or callable transformer to apply upon a match.

    Returns:
        tuple[str, dict[str, Any]]: A tuple containing the transformed line (with terminal clearing escape sequences)
            and a dictionary of extracted named regex groups (empty if no match or error occurs).
    """
    # REGEX PATTERN SEARCH & MATCH EVALUATION
    # Searches the input line for a match against the compiled regular expression pattern.
    match = pattern.search(line)
    if not match:
        return line, {}

    # GROUP EXTRACTION & ARGUMENT MAPPING
    # Extracts named keyword groups and positional group tuples from the regex match.
    kwargs = match.groupdict()
    args = match.groups()

    # DYNAMIC FORMATTING & EXCEPTION FIREWALL
    # Attempts to format or transform the matched elements, returning the result with a terminal clear sequence.
    try:
        formatted = format_match(target=target, kwargs=kwargs, args=args)
        return f"{formatted}\033[K", kwargs
    except (KeyError, ValueError, IndexError, TypeError) as e:
        # FORMATTING EXCEPTION HANDLING & FALLBACK
        # Reports a warning when dynamic formatting fails and falls back to the original line.
        report_status(
            state="warn",
            message=f"Formatting template error: {e}. Falling back to original line.",
            context=LogContext(
                component="interface.interceptor",
                log_path=log_path,
                silent=False,
                trace_id="interceptor",
                actor=context.get("user"),
                exception=str(e),
                payload={"line": line.strip()},
            ),
        )
        return line, kwargs
