import re
from typing import Any


# SYSTEM UTILITIES SUBSYSTEM: DATA AUDITING & TOKEN SANITIZATION
# This utility audits and sanitizes inbound dictionaries by transforming string values
# into lowercase underscore-delimited tokens, safely casting numerics, and ensuring null safety.
# [>] EXECUTING DATA AUDITING & SANITIZATION
def sanitize_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Audits and sanitizes the entire inbound data bucket.
    Transforms strings into lowercase underscore-delimited alphanumeric tokens,
    safely casts numeric types, and ensures null safety.

    Args:
        data (dict[str, Any]): The raw dictionary containing data attributes to sanitize.

    Returns:
        dict[str, Any]: A new dictionary containing fully audited, sanitized values.
    """
    # SANITIZED MAP CONTAINER INITIALIZATION
    # Initializes the target dictionary container for sanitized key-value pairs.
    sanitized_map: dict[str, Any] = {}

    # INBOUND DATA ITERATION & TRANSFORMATION
    # Iterates over dictionary items, applying string tokenization, numeric casting,
    # and fallback string representation or null-safety handling.
    for key, value in data.items():
        if isinstance(value, str):
            # STRING TOKENIZATION & NORMALIZATION
            # Converts strings to lowercase, replaces spaces with underscores,
            # and strips out non-alphanumeric characters except underscores.
            sanitized_map[key] = re.sub(
                r"[^a-z0-9_]", "", value.lower().replace(" ", "_")
            )

        elif value is not None:
            # ATOMIC TYPE VERIFICATION: NUMERIC HARDENING
            # Safely casts numeric types while preventing ValueErrors
            # during downstream formatting directives like '{key:02d}'.
            try:
                sanitized_map[key] = int(value)
            except (ValueError, TypeError):
                sanitized_map[key] = str(value)
        else:
            # NULL-SAFETY ASSIGNMENT
            # Assigns an empty string fallback for null/None values.
            sanitized_map[key] = ""

    return sanitized_map
