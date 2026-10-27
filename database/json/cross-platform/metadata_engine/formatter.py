from typing import Any


# DATA CONTAINER SUBSYSTEM: UNIT CONVENTION FORMATTING & REGISTRY
# This utility evaluates leaf keys against configured unit definitions,
# applying floating-point precision rounding and standardized unit suffixes.
# [>] EXECUTING UNIT FORMATTING PIPELINE
def apply_unit_formatting(
    key: str, value: Any, unit_configs: list[dict[str, list[str] | str]] | None
) -> Any:
    """
    Appends units to values based on the leaf key name according to unit configurations.

    Args:
        key (str): The terminal leaf key name.
        value (Any): The value to format.
        unit_configs (list[dict[str, list[str] | str]] | None): A list of dictionaries defining units for specific keys
            (e.g., [{'keys': ['bitrate'], 'unit': 'kb/s'}]).

    Returns:
        Any: The formatted value with unit suffix or the original value if no match/null.
    """
    # FORMATTING GATE: ATOMIC SIGNAL VALIDATION
    # Bypasses transformation if no configurations exist or if the value is null/empty.
    # [>] EVALUATING FORMATTING ELIGIBILITY
    if not unit_configs or value in [None, ""]:
        return value

    # CONFIGURATION TRAVERSAL: RULE-BASED MATCHING
    # Iterates through unit definitions to find an affinity between the leaf key and unit.
    # [>] SCANNING UNIT REGISTRY
    for config in unit_configs:
        target_keys = config.get("keys", [])
        unit = config.get("unit", "")

        # AFFINITY MATCH: LEAF-KEY VERIFICATION
        # If the current key is registered within this unit scope, initiate transformation.
        if isinstance(target_keys, list) and key in target_keys:

            # NUMERIC PRECISION REFINEMENT: FLOAT STANDARDIZATION
            # Rounds floats to 3 decimal places to prevent excessive precision noise in the UI.
            # [>] EXECUTING ROUNDING LOGIC
            if isinstance(value, float):
                value = round(value, 3)

            # TRANSFORMATION PIPELINE: ATOMIC STRING CONSOLIDATION
            # Returns formatted signal, stripping whitespace if unit is empty.
            # [+] APPLYING UNIT SUFFIX
            return f"{value} {unit}".strip()

    # FALLBACK EXIT: NO MATCHING RULE
    # Returns raw signal if key does not require unit normalization, preventing unit leakage.
    return value
