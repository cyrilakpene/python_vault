from typing import Any


# SYSTEM UTILITIES SUBSYSTEM: DATA TYPE INFERENCE & HEURISTIC DOWNCASTING
# This utility infers the underlying primitive data type (int, float, str, or None) from raw inputs
# by applying string sanitization, formatting cleanup, and numeric conversion heuristics.
# [>] EXECUTING TYPE INFERENCE
def infer_type(val: Any) -> int | float | str | None:
    """
    Infers the primitive data type of a raw value by sanitizing strings and attempting numeric downcasting.

    Args:
        val (Any): The raw value to analyze and convert.

    Returns:
        Union[int, float, str, None]: The downcast integer, float, original/fallback string, or None.
    """
    # NULL-SAFETY VALIDATION
    # Returns None immediately if the input value is null.
    if val is None:
        return None

    # DATA SANITIZATION & NORMALIZATION
    # Converts the value to a string, strips whitespace, and removes commas and percentage symbols.
    clean_val = str(val).strip().replace(",", "").replace("%", "")

    # HEURISTIC DOWNCASTING: INTEGER CONVERSION
    # Attempts integer conversion for discrete counts, accounting for optional sign markers.
    if clean_val.lstrip("-+").isdigit():
        return int(clean_val)

    # HEURISTIC DOWNCASTING: FLOAT CONVERSION
    # Attempts float conversion for rates, ratios, and decimal times, falling back to string on failure.
    try:
        return float(clean_val)
    except ValueError:
        # STRING FALLBACK
        # Returns the original input value as a string fallback if no numeric pattern matches.
        return val
