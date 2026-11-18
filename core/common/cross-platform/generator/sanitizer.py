import re
from typing import Any


# SYSTEM UTILITIES SUBSYSTEM: DATA AUDITING & TOKEN SANITIZATION
# This utility audits and sanitizes inbound dictionaries by transforming string values
# into underscore-delimited tokens (with optional case and punctuation preservation), safely casting numerics, and ensuring null safety.
# [>] EXECUTING DATA AUDITING & SANITIZATION
def sanitize_data(
    data: dict[str, Any], 
    preserve_case: bool = False, 
    preserve_punctuation: bool = False
) -> dict[str, Any]:
    """
    Audits and sanitizes the entire inbound data bucket[cite: 5].
    Transforms strings into underscore-delimited tokens (preserving case and punctuation if specified),
    safely casts numeric types, and ensures null safety[cite: 5].

    Args:
        data (dict[str, Any]): The raw dictionary containing data attributes to sanitize[cite: 5].
        preserve_case (bool): If True, preserves the original casing of string values. Default is False[cite: 5].
        preserve_punctuation (bool): If True, preserves specific punctuation like '?' in string values. Default is False.

    Returns:
        dict[str, Any]: A new dictionary containing fully audited, sanitized values[cite: 5].
    """
    # SANITIZED MAP CONTAINER INITIALIZATION
    # Initializes the target dictionary container for sanitized key-value pairs[cite: 5].
    sanitized_map: dict[str, Any] = {}

    # INBOUND DATA ITERATION & TRANSFORMATION
    # Iterates over dictionary items, applying string tokenization, numeric casting,
    # and fallback string representation or null-safety handling[cite: 5].
    for key, value in data.items():
        if isinstance(value, str):
            if preserve_case:
                # STRING TOKENIZATION & NORMALIZATION (PRESERVE CASE & OPTIONAL PUNCTUATION)
                # Replaces spaces and hyphens with underscores, and strips out non-alphanumeric
                # characters except underscores (and '?' if enabled) while keeping original character casing[cite: 5].
                pattern = r"[^a-zA-Z0-9_?]" if preserve_punctuation else r"[^a-zA-Z0-9_]"
                sanitized_map[key] = re.sub(
                    pattern, "", value.replace(" ", "_").replace("-", "_")
                )
            else:
                # STRING TOKENIZATION & NORMALIZATION (LOWERCASE DEFAULT & OPTIONAL PUNCTUATION)
                # Converts strings to lowercase, replaces spaces and hyphens with underscores,
                # and strips out non-alphanumeric characters except underscores (and '?' if enabled)[cite: 5].
                pattern = r"[^a-z0-9_?]" if preserve_punctuation else r"[^a-z0-9_]"
                sanitized_map[key] = re.sub(
                    pattern, "", value.lower().replace(" ", "_").replace("-", "_")
                )

        elif value is not None:
            # ATOMIC TYPE VERIFICATION: NUMERIC HARDENING
            # Safely casts numeric types while preventing ValueErrors
            # during downstream formatting directives like '{key:02d}'[cite: 5].
            try:
                sanitized_map[key] = int(value)
            except (ValueError, TypeError):
                sanitized_map[key] = str(value)
        else:
            # NULL-SAFETY ASSIGNMENT
            # Assigns an empty string fallback for null/None values[cite: 5].
            sanitized_map[key] = ""

    return sanitized_map

