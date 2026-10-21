from typing import Any, cast


# STRING LIST PARSING & DELIMITED TOKEN SANITIZATION ENGINE
# Transforms comma-separated string payloads into a cleaned list of non-empty string tokens
# by stripping surrounding whitespace and filtering out blank entries.
def parse_list_str(v: str) -> list[str]:
    """
    Parses a comma-separated string into a list of cleaned string tokens.

    Args:
        v: Raw inbound comma-separated string payload to tokenize.

    Returns:
        list[str]: A list of sanitized, non-empty string tokens extracted from the input.
    """
    # DELIMITED SPLITTING, WHITESPACE STRIPPING & EMPTY TOKEN FILTERING
    # Splits the input payload on commas, strips whitespace from each token,
    # and discards empty strings to yield a clean string collection.
    return [s.strip() for s in v.split(",") if s.strip()]


# DATA EXTRACTION & INTEGER LIST PARSING ENGINE
# This transformation utility normalizes raw string inputs into typed, validated integer lists.
# By combining delimiter sanitization with a dual-path parser—supporting both positional template
# overlays on pre-existing field defaults and dynamic array creation—it prevents index exceptions
# and maintains data integrity across sparse, custom, or malformed input vectors.
def parse_list_int(v: str, field: dict[str, Any] | None) -> list[int]:
    """
    DATA NORMALIZATION: SAFE INTEGER EXTRACTION WITH COGNIZANT COUPLING

    This utility transforms raw string representations of lists/CSVs into
    validated integer arrays. It implements 'Clean-Catch' logic to ensure
    system stability even when encountering malformed input. If the operator
    inputs sparse parameters separated by commas, it parses empty slots as
    placeholders, merging values positionally over the matching default coordinates.
    When no baseline array template exists, it dynamically allocates a new array
    from valid numeric tokens to prevent index bound exceptions.

    Args:
        v: Raw inbound string representation of numbers, CSV, or stringified list/tuple.
        field: Configuration schema dictionary containing field metadata and optional default values.

    Returns:
        list[int]: A validated list of parsed integers reconciled against field default templates.
    """

    # [>] SYNTAX DE-ESCALATION
    # We strip common list and tuple delimiters (brackets and parentheses) to handle
    # raw CSV strings ("1, 2, 3"), stringified lists ("[1, 2]"), and stringified tuples ("(0, 5)").
    clean_v = (
        v.replace("[", "").replace("]", "").replace("(", "").replace(")", "").strip()
    )

    # POSITION OVERLAY FIREWALL: EXTRACT BASELINE SHAPE
    # We look up the active field's default state via scope closure enclosure.
    # If the inbound default is a list, we extract its values as our baseline matrix template.
    field = field or {}
    default_val = field.get("default")
    safe_default = (
        [int(x) for x in cast(list[Any], default_val)]
        if isinstance(default_val, list)
        else []
    )

    # VACUUM EXIT: EMPTY INPUT FALLBACK
    # If the operator provides an empty string (e.g., pressing Enter without input),
    # we immediately yield the safe baseline default array.
    if not clean_v:
        return safe_default

    # SPLIT AND CHOP FRACTIONS POSITIONALLY
    # We segment the sanitized string by commas to expose individual positional tokens.
    fragments = clean_v.split(",")

    # DUAL-PATHING PARSER: TEMPLATE OVERLAY vs. DYNAMIC ALLOCATION
    if safe_default:
        # PATH A: SURGICAL ARRAY OVERLAY (POSITION COUPLING)
        # When a baseline array template exists, we clone the default coordinates
        # and positionally overwrite active elements with user-provided overrides.
        reconciled_list = list(safe_default)
        for i, raw in enumerate(fragments):
            # [>] EVALUATING DIMENSIONAL BOUNDS
            # We drop out early if inbound input dimensions exceed the baseline matrix footprint.
            if i >= len(reconciled_list):
                break

            # WHITESPACE STRIPPING: Removes leading/trailing noise.
            # ASSIGNMENT EXPRESSION (Walrus): Stores the cleaned string token.
            # NUMERIC INTEGRITY: We use .isdigit() on the absolute value (lstrip("-"))
            #    to support negative integers while filtering out alpha/symbol noise.
            if (val := raw.strip()) and val.lstrip("-").isdigit():
                # SURGICAL INDEX COUPLING: OVERWRITING ACTIVE ELEMENT
                # Explicit empty slots are skipped, natively retaining default coordinates.
                reconciled_list[i] = int(val)

        return reconciled_list

    # PATH B: DYNAMIC ARRAY ALLOCATION
    # When no list baseline exists (e.g., scalar/tuple defaults or un-templated fields),
    # we dynamically parse and append valid integer tokens to avoid index assignment bounds errors.
    parsed: list[int] = []
    for raw in fragments:
        if (val := raw.strip()) and val.lstrip("-").isdigit():
            parsed.append(int(val))

    # PARSED VECTOR RETURN
    # Yields dynamically populated integer vector when no default matrix overlay is available.
    return parsed


# TUPLE CASTING & STRUCTURAL IMMUTABILITY ENGINE
# This transformation gateway wraps raw input parsing within immutable tuple guarantees.
# By combining underlying string-to-list extraction, fallback scalar-to-range expansion,
# and tuple coercion, it delivers static numeric bounds required by downstream slicing systems.
def parse_tuple_int(v: str, field: dict[str, Any] | None) -> tuple[int, ...]:
    """
    TYPE CASTING GATEWAY: STRING-TO-INT TUPLE CONVERTER

    This utility orchestrates the ingestion of raw string data, routes it
    through an integer-list parsing pipeline, and freezes the output into
    an immutable tuple. It ensures structural rigidity for downstream processes
    requiring static numeric arrays or positional slice ranges.

    Args:
        v: Raw inbound string representation of numbers, CSV, or tuple formatting.
        field: Configuration schema dictionary containing field metadata and positional default settings.

    Returns:
        tuple[int, ...]: An immutable tuple of parsed integers, expanded to 2-element range coordinates where required.
    """

    # STRUCTURAL FREEZE & PIPELINE DELEGATION
    # We delegate core string parsing, delimiter stripping, and integer validation to '_parse_list_int'.
    field = field or {}
    parsed = parse_list_int(v=v, field=field)

    # DEFAULT RECOVERY & SCALAR COERCION
    # If no explicit values were supplied by the user (or parsing yielded an empty set),
    # we evaluate the field's underlying schema default to reconcile structural expectations.
    if not parsed:
        default_val = field.get("default")

        # [>] TUPLE PASSTHROUGH
        # If the default is already a structured tuple (e.g., (0, 5)), return it directly.
        if isinstance(default_val, tuple):
            return cast(tuple[int, ...], default_val)

        # [>] SCALAR-TO-RANGE EXPANSION
        # Converts scalar integer defaults (e.g. 5) into 2-tuple range bounds (0, 5)
        # to satisfy downstream slice expectations (e.g., pandas iloc positional ranges).
        if isinstance(default_val, int):
            return (0, default_val)

        return ()

    # 1-TUPLE EXPANSION
    # If the user entered a single number (or parsed a scalar default into a 1-tuple like (5,)),
    # expand it to a 2-tuple (0, N) so downstream slicing functions receive a valid range (start, end).
    if len(parsed) == 1:
        return (0, parsed[0])

    # IMMUTABLE LOCK-IN
    # Once the array is safely extracted and validated, we cast the mutable list
    # to an immutable tuple to guarantee write-protection during downstream runtime.
    return tuple(parsed)


# DATA EXTRACTION & FLOAT LIST PARSING ENGINE
# This transformation utility normalizes raw string inputs into typed, validated floating-point lists.
# By combining delimiter sanitization with a dual-path parser—supporting both positional template
# overlays on pre-existing field defaults and dynamic array creation—it prevents index exceptions
# and maintains data integrity across sparse, custom, or malformed input vectors.
def parse_list_float(v: str, field: dict[str, Any] | None) -> list[float]:
    """
    DATA NORMALIZATION: SAFE FLOAT EXTRACTION WITH COGNIZANT COUPLING

    This utility transforms raw string representations of lists/CSVs into
    validated float arrays. It implements 'Clean-Catch' logic to ensure
    system stability even when encountering malformed input. If the operator
    inputs sparse parameters separated by commas, it parses empty slots as
    placeholders, merging values positionally over the matching default coordinates.
    When no baseline array template exists, it dynamically allocates a new array
    from valid numeric tokens to prevent index bound exceptions.

    Args:
        v: Raw inbound string representation of numbers, CSV, or stringified list/tuple.
        field: Configuration schema dictionary containing field metadata and optional default values.

    Returns:
        list[float]: A validated list of parsed floats reconciled against field default templates.
    """

    # [>] SYNTAX DE-ESCALATION
    # We strip common list and tuple delimiters (brackets and parentheses) to handle
    # raw CSV strings ("1.5, 2.0"), stringified lists ("[1.0, 2.5]"), and stringified tuples "(0.0, 5.0)".
    clean_v = (
        v.replace("[", "").replace("]", "").replace("(", "").replace(")", "").strip()
    )

    # POSITION OVERLAY FIREWALL: EXTRACT BASELINE SHAPE
    # We look up the active field's default state via scope closure enclosure.
    # If the inbound default is a list, we extract its values as our baseline matrix template.
    field = field or {}
    default_val = field.get("default")
    safe_default = (
        [float(x) for x in cast(list[Any], default_val)]
        if isinstance(default_val, list)
        else []
    )

    # VACUUM EXIT: EMPTY INPUT FALLBACK
    # If the operator provides an empty string (e.g., pressing Enter without input),
    # we immediately yield the safe baseline default array.
    if not clean_v:
        return safe_default

    # SPLIT AND CHOP FRACTIONS POSITIONALLY
    # We segment the sanitized string by commas to expose individual positional tokens.
    fragments = clean_v.split(",")

    # DUAL-PATHING PARSER: TEMPLATE OVERLAY vs. DYNAMIC ALLOCATION
    if safe_default:
        # PATH A: SURGICAL ARRAY OVERLAY (POSITION COUPLING)
        # When a baseline array template exists, we clone the default coordinates
        # and positionally overwrite active elements with user-provided overrides.
        reconciled_list = list(safe_default)
        for i, raw in enumerate(fragments):
            # [>] EVALUATING DIMENSIONAL BOUNDS
            # We drop out early if inbound input dimensions exceed the baseline matrix footprint.
            if i >= len(reconciled_list):
                break

            # WHITESPACE STRIPPING & NUMERIC INTEGRITY CASTING
            if val := raw.strip():
                try:
                    reconciled_list[i] = float(val)
                except ValueError:
                    pass

        return reconciled_list

    # PATH B: DYNAMIC ARRAY ALLOCATION
    # When no list baseline exists, we dynamically parse and append valid float tokens.
    parsed: list[float] = []
    for raw in fragments:
        if val := raw.strip():
            try:
                parsed.append(float(val))
            except ValueError:
                continue

    # PARSED VECTOR RETURN
    # Yields dynamically populated float vector when no default matrix overlay is available.
    return parsed


# TUPLE CASTING & STRUCTURAL IMMUTABILITY ENGINE (FLOAT)
# This transformation gateway wraps raw input parsing within immutable tuple guarantees for floating-point values.
# By combining underlying string-to-list extraction, fallback scalar-to-range expansion,
# and tuple coercion, it delivers static floating-point bounds required by downstream systems.
def parse_tuple_float(v: str, field: dict[str, Any] | None) -> tuple[float, ...]:
    """
    TYPE CASTING GATEWAY: STRING-TO-FLOAT TUPLE CONVERTER

    This utility orchestrates the ingestion of raw string data, routes it
    through a float-list parsing pipeline, and freezes the output into
    an immutable tuple. It ensures structural rigidity for downstream processes
    requiring static numeric arrays or positional slice ranges.

    Args:
        v: Raw inbound string representation of numbers, CSV, or tuple formatting.
        field: Configuration schema dictionary containing field metadata and positional default settings.

    Returns:
        tuple[float, ...]: An immutable tuple of parsed floats, expanded to 2-element range coordinates where required.
    """

    # STRUCTURAL FREEZE & PIPELINE DELEGATION
    # We delegate core string parsing, delimiter stripping, and float validation to '_parse_list_float'.
    field = field or {}
    parsed = parse_list_float(v=v, field=field)

    # DEFAULT RECOVERY & SCALAR COERCION
    # If no explicit values were supplied by the user, we evaluate the field's underlying schema default.
    if not parsed:
        default_val = field.get("default")

        # [>] TUPLE PASSTHROUGH
        # If the default is already a structured tuple, return it directly.
        if isinstance(default_val, tuple):
            return cast(tuple[float, ...], default_val)

        # [>] SCALAR-TO-RANGE EXPANSION
        # Converts scalar numeric defaults into 2-tuple range bounds (0.0, N).
        if isinstance(default_val, (int, float)):
            return (0.0, float(default_val))

        return ()

    # 1-TUPLE EXPANSION
    # If the user entered a single number, expand it to a 2-tuple (0.0, N).
    if len(parsed) == 1:
        return (0.0, parsed[0])

    # IMMUTABLE LOCK-IN
    # Once the array is safely extracted and validated, we cast the mutable list
    # to an immutable tuple to guarantee write-protection during downstream runtime.
    return tuple(parsed)


# STRING TOKENIZATION & ARRAY PARSING ENGINE
# This utility transforms raw string representations of array-like structures into
# immutable, cleaned string tuples. By stripping structural containers and discarding
# empty fragments, it ensures predictable token extraction across CLI and file inputs.
def parse_tuple_str(v: str) -> tuple[str, ...]:
    """
    SYNTAX SANITIZER: STRING-TO-TUPLE DESERIALIZER

    This utility normalizes and parses raw string representations of array-like
    structures (e.g., '[item1, item2]' or '(item1, item2)') into a clean Python
    tuple of individual string tokens. It acts as a robust ingestion interface
    to prevent downstream parsing failures.

    Args:
        v: Raw inbound string representing an array, list, tuple, or CSV string.

    Returns:
        tuple[str, ...]: An immutable tuple of stripped, non-empty string tokens.
    """

    # CONTAINER BOUNDARY STRIPPER
    # Inbound strings often arrive wrapped in array, list, or tuple notation
    # from configuration files or CLI inputs. We aggressively strip these
    # enclosing boundary characters to isolate the raw, comma-separated tokens.
    clean_v = v.replace("[", "").replace("]", "").replace("(", "").replace(")", "")

    # TOKENIZATION & VACUUM CLEANING
    # We split the sanitized string by commas, strip leading/trailing whitespace
    # from each isolated element, and discard any empty strings resulting
    # from trailing commas (e.g., "a, b,"). Finally, we cast to an immutable tuple.
    return tuple(s.strip() for s in clean_v.split(",") if s.strip())
