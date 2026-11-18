from typing import Any

from .sanitizer import sanitize_data  # type: ignore[import-not-found]
from .context import create_context  # type: ignore[import-not-found]
from .transformer import apply_transformation  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: JOB ID GENERATION & PIPELINE ORCHESTRATION
# This utility orchestrates the end-to-end Job ID generation pipeline by coordinating data sanitization
# (with optional case and punctuation preservation), context wrapping, and schematic rule transformation.
# [>] EXECUTING JOB ID GENERATION
def generate_job_id(
    rule: str, 
    data: dict[str, Any], 
    preserve_case: bool = False, 
    preserve_punctuation: bool = False
) -> str:
    """
    Transforms raw metadata into a sanitized Job ID using a direct formatting rule.
    Coordinates data sanitization, context wrapping, and schematic rule transformation.

    Args:
        rule (str): The formatting rule string containing template variables.
        data (dict[str, Any]): The raw input metadata dictionary to sanitize and format.
        preserve_case (bool): If True, retains original string case in the generated ID. Default is False.
        preserve_punctuation (bool): If True, retains specific punctuation like '?' in the generated ID. Default is False.

    Returns:
        str: The final sanitized and formatted Job ID string.
    """
    # DATA SANITIZATION & CONTEXT PREPARATION
    # Sanitizes inbound raw data values (with optional case and punctuation preservation) and wraps them in a zero-fail default context mapping.
    sanitized_map = sanitize_data(
        data, 
        preserve_case=preserve_case, 
        preserve_punctuation=preserve_punctuation
    )
    clean_context = create_context(sanitized_map)

    # RULE TRANSFORMATION EXECUTION
    # Applies the formatting rule against the clean context to yield the final transformed Job ID.
    return apply_transformation(rule, clean_context)
