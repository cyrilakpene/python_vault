import re
from collections import defaultdict
from typing import Any


# ARCHITECTURAL GATEKEEPER: ATOMIC IDENTITY TRANSFORMER
# This engine serves as the "Filesystem Sanitizer." It transforms volatile
# metadata into deterministic, shell-safe, and filesystem-compliant Job IDs.
# By enforcing strict character stripping and numeric casting, it ensures
# that generated IDs can be used as directory names or database keys without
# triggering escaping errors or injection vulnerabilities.
def generate_job_id(rule: str, data: dict[str, Any]) -> str:
    """
    Transforms raw metadata into a sanitized Job ID using a direct formatting rule.
    Implements kinetic data sanitization and atomic type enforcement for OS safety.
    """

    # KINETIC DATA SANITIZATION: REGEX PERIMETER CONTROL
    # We audit the entire inbound data bucket before the transformation phase.
    # This proactive cleaning ensures that any variable requested by the
    # 'rule' is already lowercase, underscore-delimited, and alpha-numeric compliant.
    # [~] INITIALIZING SANITIZED MAP
    sanitized_map: dict[str, Any] = {}

    for key, value in data.items():
        if isinstance(value, str):
            # LOWERCASE -> UNDERSCORE -> ALPHA-NUMERIC STRIP
            # We neutralize special characters and spaces to prevent shell-injection
            # or filesystem path breakages.
            sanitized_map[key] = re.sub(
                r"[^a-z0-9_]", "", value.lower().replace(" ", "_")
            )

        elif value is not None:
            # ATOMIC TYPE VERIFICATION: NUMERIC HARDENING
            # Essential for preventing ValueErrors during '{key:02d}' or
            # similar formatting directives in the 'rule' string.
            # [d] CASTING NUMERIC VALUE FOR KEY: {key}
            try:
                sanitized_map[key] = int(value)
            except (ValueError, TypeError):
                sanitized_map[key] = str(value)
        else:
            # NULL-SAFETY ASSIGNMENT
            sanitized_map[key] = ""

    # ZERO-FAIL CONTEXT INITIALIZATION: DEFAULTDICT WRAPPER
    # We utilize a 'defaultdict' to provide a "Graceful Fallback" for missing keys.
    # If the 'rule' string references a key absent from the 'data' bucket,
    # the engine returns an empty string instead of triggering a KeyError.
    clean_context: defaultdict[str, Any] = defaultdict(str, sanitized_map)

    # SCHEMATIC TRANSFORMATION: RULE INJECTION
    # We apply the 'rule' template string directly against the cleaned context.
    # This phase performs the final assembly and collapses structural redundancies.
    # [>] APPLYING FORMAT RULE: {rule}
    try:
        # FORMAT_MAP: Performs the variable injection.
        generated_id: str = rule.format_map(clean_context)

        # KINETIC REFINEMENT: UNDERSCORE COLLAPSE
        # We collapse '___' into '_' which occurs when optional rule fragments
        # are empty. We then strip leading/trailing underscores for a clean ID.
        return re.sub(r"_+", "_", generated_id).strip("_")

    except Exception as e:
        # FAIL-SAFE FALLBACK: ERROR EMISSION
        # In the event of a syntax error within the 'rule' string (e.g., unmatched
        # brackets), we return a flagged ID to prevent silent failure.
        # [x] RULE RESOLUTION FAILURE: {str(e)}
        return f"id_resolution_error_{str(e).replace(' ', '_')}".strip("_")
