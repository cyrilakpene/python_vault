import re
from typing import Any


# SYSTEM UTILITIES SUBSYSTEM: RULE TRANSFORMATION & FORMAT MAPPING
# This utility applies format mapping rules against clean template contexts, refines generated tokens
# by collapsing consecutive underscores, and provides robust fail-safe error handling.
# [>] EXECUTING RULE TRANSFORMATION
def apply_transformation(rule: str, clean_context: Any) -> str:
    """
    Applies format mapping against the clean context, collapses consecutive
    underscores, strips leading/trailing characters, and intercepts formatting exceptions.

    Args:
        rule (str): The format rule string containing template substitution keys.
        clean_context (Any): The sanitization context mapping providing variable values.

    Returns:
        str: The transformed and refined output string, or an error identifier upon failure.
    """
    try:
        # FORMAT_MAP: VARIABLE INJECTION
        # Performs dynamic variable injection using the provided context mapping.
        generated_id: str = rule.format_map(clean_context)

        # KINETIC REFINEMENT: UNDERSCORE COLLAPSE & STRIPPING
        # Collapses consecutive underscore sequences into single underscores and strips boundary markers.
        return re.sub(r"_+", "_", generated_id).strip("_")

    except Exception as e:
        # FAIL-SAFE FALLBACK: ERROR EMISSION
        # Intercepts formatting errors, sanitizes the exception message into token format,
        # and returns a descriptive error fallback identifier.
        return f"id_resolution_error_{str(e).replace(' ', '_')}".strip("_")
