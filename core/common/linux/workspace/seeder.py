import re
import shutil
from pathlib import Path

from .paths import resolve_template_source  # type: ignore[import-not-found]


# WORKSPACE SUBSYSTEM: INTERNAL VERSION EXTRACTION
# Scans file contents for explicit key-value version declarations (e.g., "version": "1.0.1",
# VERSION = "1.0.1") while strictly ignoring unrelated prose mentioning the word version.
# [>] EXECUTING INTERNAL VERSION EXTRACTION
def _extract_version(file_path: Path) -> str | None:
    """
    Extracts the version string defined inside the file.

    Args:
        file_path (Path): Path to the file to inspect.

    Returns:
        str | None: The extracted version string if found, otherwise None.
    """
    # FILE EXISTENCE GUARD
    # Returns early if the target file does not exist on disk.
    if not file_path.exists():
        return None

    # REGEX VERSION EXTRACTION & FILE READING
    # Reads file contents using UTF-8 encoding and applies regular expression pattern matching
    # to isolate explicit version identifiers.
    try:
        content = file_path.read_text(encoding="utf-8")
        pattern = r'(?:["\']?version["\']?\s*[:=]\s*["\']?)(v?\d+\.\d+(?:\.\d+)?[\w-]*)'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # MATCH RESOLUTION & RETURN
            # Returns the captured version string group if a valid pattern match is found.
            return match.group(1)
    except Exception:
        # EXCEPTION HANDLING: SAFE BYPASS
        # Safely catches any file reading, decoding, or regex parsing exceptions.
        pass

    # VERSION ABSENCE FALLBACK
    # Returns None if no valid version declaration is discovered.
    return None


# WORKSPACE SUBSYSTEM: SEMANTIC VERSION PARSING
# Converts extracted version strings into integer tuples for accurate numeric comparison.
# [>] EXECUTING SEMANTIC VERSION PARSING
def _parse_version(version_str: str | None) -> tuple[int, ...] | None:
    """
    Parses a semantic version string (e.g., '1.0.1' or 'v1.2.3') into a tuple of integers.

    Args:
        version_str (str | None): Raw version string to parse.

    Returns:
        tuple[int, ...] | None: Tuple of version integers, or None if unparseable.
    """
    # EMPTY VERSION GUARD
    # Exits early if no version string is provided.
    if not version_str:
        return None

    # NUMERIC TUPLE CONVERSION & CLEANING
    # Strips whitespace, removes leading version specifier prefixes ('v' or 'V'),
    # and matches leading dot-separated numeric segments before converting them into comparable integer tuples.
    try:
        cleaned = version_str.strip().lstrip("vV")
        # Extract only the leading numeric dot-separated segment before any pre-release suffix
        numeric_part = re.match(r"^\d+(?:\.\d+)*", cleaned)
        if numeric_part:
            # TUPLE MAPPING & RETURN
            # Maps each extracted numeric string segment to an integer and returns them as a comparable tuple.
            return tuple(map(int, numeric_part.group(0).split(".")))
    except ValueError:
        # EXCEPTION HANDLING: SAFE BYPASS
        # Safely catches casting or ValueError exceptions during integer conversion.
        pass

    # PARSING FAILURE FALLBACK
    # Returns None if the version string cannot be successfully parsed into numeric components.
    return None


# WORKSPACE SUBSYSTEM: TEMPLATE SEEDING & FILE SYNCHRONIZATION
# This utility inspects workspace target directories and securely copies missing configuration
# or data files from resolved source paths, updating existing files only when a newer template version is detected.
# [>] EXECUTING TEMPLATE FILE SEEDING
def seed_files(
    target_dir: Path,
    default_templates_dir: Path,
    files: list[str] | None,
    custom_sources: dict[str, Path | str] | None = None,
) -> None:
    """
    Seeds target directory with template files if the user files do not already exist,
    or updates them if the source template contains a newer internal version.

    Args:
        target_dir (Path): The destination directory (config or data dir).
        default_templates_dir (Path): The fallback system templates directory.
        files (list[str] | None): List of filenames to check and copy.
        custom_sources (dict[str, Path | str], optional): Explicit filename-to-source mapping dictionary.
    """
    # FILE LIST VALIDATION GUARD
    # Exits early if no files are designated for seeding.
    if not files:
        return

    # TARGET DIRECTORY CREATION
    # Ensures destination directories exist with appropriate parent structures.
    target_dir.mkdir(parents=True, exist_ok=True)

    # FILE ITERATION & CONDITIONAL COPYING
    # Iterates through target files, copying missing files or updating outdated versions.
    for filename in files:
        user_file = target_dir / filename

        # TEMPLATE SOURCE RESOLUTION
        # Resolves the exact source path using custom overrides or default system directories.
        source_file = resolve_template_source(
            filename, default_templates_dir, custom_sources
        )

        # SOURCE EXISTENCE GUARD
        # Skips processing if the resolved template source file does not exist.
        if not source_file.exists():
            continue

        # INITIAL SEEDING EXECUTION
        # Copies template source to user workspace if the user file does not exist yet.
        if not user_file.exists():
            shutil.copy(source_file, user_file)
            continue

        # INTERNAL VERSION EVALUATION & UPDATE EXECUTION
        # Extracts and compares internal versions; backs up user file and overwrites only if source version is strictly newer.
        source_version = _parse_version(_extract_version(source_file))
        user_version = _parse_version(_extract_version(user_file))

        if source_version and user_version and source_version > user_version:
            # USER FILE BACKUP & TEMPLATE OVERWRITE EXECUTION
            # Safely backs up the outdated user configuration before deploying the newer template version.
            backup_file = user_file.with_suffix(user_file.suffix + ".bak")
            shutil.copy(user_file, backup_file)
            shutil.copy(source_file, user_file)
