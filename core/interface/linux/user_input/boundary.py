from typing import Any, cast


# BOUNDARY VALIDATION & CONSTRAINT ENFORCEMENT ENGINE
# This validation engine enforces runtime range, length, and set-membership constraints across
# primitive and complex data types. By recursively inspecting collections, measuring string buffer lengths,
# evaluating numeric magnitudes, and validating categorical choice sets, it guarantees that inbound values
# adhere strictly to schema operational boundaries before entering downstream pipelines.
def enforce_boundaries(v: Any, field: dict[str, Any]) -> None:
    """
    UNIVERSAL BOUNDARY & CHOICE GUARD

    This validator enforces strict 'min', 'max', and 'choices' constraints
    across various data types. It acts as a final sanity check to ensure
    inbound data resides within the operational parameters defined by the
    schema, preventing "out-of-bounds" errors in downstream processes.

    Args:
        v: Data payload value of scalar, string, or collection type to validate.
        field: Configuration schema dictionary defining boundary bounds ('min', 'max', 'choices').

    Raises:
        ValueError: If array dimensions, string lengths, numeric magnitudes, or categorical choices
            violate the constraints defined within the schema.
    """

    # [>] PARAMETER EXTRACTION
    # We retrieve the specific constraints from the field definition.
    # These can apply to numeric magnitudes, string lengths, or
    # collection sizes depending on the context.
    min_val = field.get("min")
    max_val = field.get("max")
    choices = field.get("choices")

    # RECURSIVE LIST HANDLING: NESTED INTEGRITY
    # If the input is a collection, we apply the boundary logic to every
    # individual element. This ensures that a single out-of-bounds item
    # cannot contaminate an otherwise valid list.
    if isinstance(v, (list, tuple)):
        safe_list = cast(list[Any], v)
        v_len = len(safe_list)
        if min_val is not None and v_len < min_val:
            raise ValueError(
                f"Array dimension too short ({v_len} items). Expected at least {min_val}."
            )
        if max_val is not None and v_len > max_val:
            raise ValueError(
                f"Array dimension too long ({v_len} items). Maximum allowed is {max_val}."
            )

        for item in safe_list:
            # [>] RECURSIVE DESCENT
            enforce_boundaries(item, field)
        return

    # CHOICE VALIDATION: SET MEMBERSHIP
    # If the schema defines a discrete set of permitted values, we perform
    # a high-speed membership check. This is the primary filter for
    # categorical data and operational flags.
    if choices is not None:
        # CHOICE NORMALIZATION: DICTIONARY UNWRAPPER
        # Safely resolves scalar choice keys if choices contain unhashable dictionary objects.
        normalized_choices: list[Any] = [
            c["name"] if isinstance(c, dict) and "name" in c else c for c in choices
        ]

        if v not in normalized_choices:
            # [>] ERROR FORMATTING
            # We stringify the choices to provide the user with clear
            # terminal feedback on what the expected inputs were.
            allowed_str = ", ".join([str(c) for c in normalized_choices])
            raise ValueError(f"{v!r} is invalid. Must be one of: [{allowed_str}]")

    # COMPARATIVE BOUNDARIES: MULTIMODAL MAGNITUDE CHECKS
    # We branch our validation logic based on the data type. This allows the
    # 'min' and 'max' keys to be polymorphic: they enforce numeric range
    # for integers/floats, but enforce character counts for strings.
    if isinstance(v, str):
        # STRING LENGTH VALIDATION: BUFFER OVERFLOW PREVENTION
        # For strings, we measure the character count. This is vital for
        # ensuring that inbound text fits within database constraints or
        # UI display limits.
        v_len = len(v)

        # [>] LOWER BOUND (LENGTH)
        if min_val is not None and v_len < min_val:
            raise ValueError(
                f"Input is too short ({v_len} chars). Minimum length is {min_val}."
            )

        # [>] UPPER BOUND (LENGTH)
        if max_val is not None and v_len > max_val:
            raise ValueError(
                f"Input is too long ({v_len} chars). Maximum allowed is {max_val}."
            )

    elif isinstance(v, (int, float)):
        # NUMERIC VALUE VALIDATION: MAGNITUDE CONTROL
        # For numeric types, we evaluate the absolute value against the
        # defined thresholds. This ensures that quantitative inputs (like
        # bitrates, frame counts, or timestamps) stay within safe
        # operational limits.

        # [>] LOWER BOUND (VALUE)
        if min_val is not None and v < min_val:
            raise ValueError(f"Value {v!r} is too low. Minimum allowed is {min_val}.")

        # [>] UPPER BOUND (VALUE)
        if max_val is not None and v > max_val:
            raise ValueError(f"Value {v!r} is too high. Maximum allowed is {max_val}.")
