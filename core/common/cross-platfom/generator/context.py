from collections import defaultdict
from typing import Any


# SYSTEM UTILITIES SUBSYSTEM: TEMPLATE CONTEXT WRAPPER
# This utility wraps sanitized data dictionaries in a zero-fail defaultdict
# to provide graceful fallbacks for missing keys during template string injection.
# [>] EXECUTING CONTEXT CREATION
def create_context(sanitized_map: dict[str, Any]) -> defaultdict[str, Any]:
    """
    Wraps the sanitized data dictionary in a defaultdict to provide
    graceful fallbacks for missing keys during template string injection.

    Args:
        sanitized_map (dict[str, Any]): The sanitized data mapping to wrap.

    Returns:
        defaultdict[str, Any]: A defaultdict providing empty string fallbacks for missing keys.
    """
    # ZERO-FAIL CONTEXT INITIALIZATION: DEFAULTDICT WRAPPER
    # Wraps the data map in a defaultdict with a default string factory
    # to prevent KeyError exceptions during dynamic template formatting.
    return defaultdict(str, sanitized_map)
