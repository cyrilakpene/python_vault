import re
from typing import Callable

from .formatter import format_match  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: LINE INTERCEPTION & REGEX TRANSFORMATION
# This utility evaluates text lines against compiled regex patterns, extracts matched groups,
# applies dynamic formatting or callable transformations, and handles exceptions with safe fallbacks.
# [>] EXECUTING LINE INTERCEPTION
def intercept_line(
    line: str, pattern: re.Pattern[str], target: str | Callable[..., str]
) -> str:
    """
    Evaluates text lines against compiled regex patterns and applies dynamic transformations.

    Args:
        line (str): The raw text line to evaluate and intercept.
        pattern (re.Pattern[str]): The compiled regular expression pattern to search against the line.
        target (str | Callable[..., str]): The formatting string template or callable transformer to apply upon a match.

    Returns:
        str: The transformed line with terminal clearing escape sequences appended, or the original line if no match or error occurs.
    """
    # REGEX PATTERN SEARCH & MATCH EVALUATION
    # Searches the input line for a match against the compiled regular expression pattern.
    match = pattern.search(line)
    if not match:
        return line

    # GROUP EXTRACTION & ARGUMENT MAPPING
    # Extracts named keyword groups and positional group tuples from the regex match.
    kwargs = match.groupdict()
    args = match.groups()

    # DYNAMIC FORMATTING & EXCEPTION FIREWALL
    # Attempts to format or transform the matched elements, returning the result with a terminal clear sequence.
    try:
        formatted = format_match(target=target, kwargs=kwargs, args=args)
        return f"{formatted}\033[K"
    except (KeyError, ValueError, IndexError, TypeError):
        return line
