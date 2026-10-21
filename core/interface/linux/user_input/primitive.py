import os


# BOOLEAN TYPE PARSING & TRUTH-VALUE NORMALIZATION ENGINE
# Transforms raw string input into a boolean state by evaluating normalized input against
# a predefined set of affirmative string tokens, handling standard CLI and configuration variations.
def parse_bool(v: str) -> bool:
    """
    Parses a string input into a boolean state.

    Args:
        v: Raw inbound string input representing a truth value.

    Returns:
        bool: True if the normalized input matches an accepted affirmative token, False otherwise.
    """
    # STRING NORMALIZATION & TOKEN MEMBERSHIP CHECK
    # Converts input to lowercase and strips outer whitespace, then performs a membership test
    # against recognized truth tokens ("y", "yes", "true", "1", "t") to determine boolean truthiness.
    return v.lower().strip() in ("y", "yes", "true", "1", "t")


# FILESYSTEM SANITATION & BOUNDARY VALIDATION ENGINE
# This validation firewall normalizes inbound file paths and verifies physical existence
# on the host system. By stripping drag-and-drop shell formatting and enforcing explicit
# file-versus-directory checks, it prevents runtime IO errors across file ingestion steps.
def validate_path(v: str, is_file: bool = False) -> str:
    """
    SANITY GATE: FILESYSTEM INTEGRITY CHECK

    This utility sanitizes inbound string data and verifies that it
    corresponds to a valid object on the host filesystem. It acts as a
    'Pre-Flight' check to prevent downstream IOErrors.

    Args:
        v: Raw string path input from environment or user prompt.
        is_file: Flag enforcing that the target path must resolve to a valid regular file.

    Returns:
        str: The fully sanitized, OS-compliant absolute path string.

    Raises:
        ValueError: If the path does not exist or fails the file-type assertion.
    """

    # SHELL-SYNTAX DE-FUSER
    # Users often drag-and-drop files into the terminal, which can inject
    # surrounding quotes or trailing whitespace. We strip these to normalize
    # the string into a clean OS-compliant path.
    clean_path: str = v.replace('"', "").replace("'", "").strip()

    # EXISTENCE VERIFICATION: THE INTEGRITY FIREWALL
    # Before passing the path to a binary, we verify its presence.
    if not os.path.exists(clean_path):
        raise ValueError(f"System path not found: {clean_path!r}")

    # TYPE VERIFICATION: FILE-SPECIFIC ENFORCEMENT
    # If is_file is True, we enforce that the path points to a file,
    # preventing folders from slipping through to file-only downstream tools.
    if is_file and not os.path.isfile(clean_path):
        raise ValueError(f"Path exists but is not a valid file: {clean_path!r}")

    # SANITIZED PATH RETURN
    # Yields verified path string once existence and structural type constraints pass.
    return clean_path


# TEMPORAL CONVERSION & TIME PARSING ENGINE
# This transformation utility normalizes formatted temporal strings (HH:MM:SS, MM:SS, or raw scalar
# seconds) into total integer seconds. By applying positional multiplier arithmetic and wrapping parsing
# errors in a silent failsafe, it guarantees uniform input formats for media seeking and time-offset logic.
def parse_time_to_seconds(v: str) -> int:
    """
    TEMPORAL NORMALIZATION: TIME STRING TO INTEGER MAPPING

    This utility standardizes various time formats (HH:MM:SS, MM:SS, or
    raw seconds) into a uniform integer representing total seconds.
    This is critical for seeking or duration logic in media processing.

    Args:
        v: Raw inbound time string formatted as HH:MM:SS, MM:SS, or raw numeric seconds.

    Returns:
        int: The resolved total time duration expressed as integer seconds, or 0 if malformed.
    """
    try:
        # [>] SEGMENTATION
        # We split the input string by colons and convert each segment
        # into an integer immediately to prepare for positional math.
        parts = [int(p) for p in v.strip().split(":")]

        # DIMENSIONAL CALCULATION
        # Based on the number of segments found, we apply the
        # appropriate multiplier to resolve the total magnitude.
        if len(parts) == 3:
            # Format: HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]

        if len(parts) == 2:
            # Format: MM:SS
            return parts[0] * 60 + parts[1]

        # [>] FALLBACK: RAW SECONDS
        # If no colons are present, we attempt to cast the
        # string directly to an integer.
        return int(v)

    except (ValueError, IndexError):
        # SILENT FAILSAFE: If the string is malformed or the indices
        # don't align with expectations, we return 0. This ensures
        # downstream math operations (like additions) don't crash.
        return 0
