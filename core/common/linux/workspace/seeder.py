import shutil
from pathlib import Path

from .paths import resolve_template_source  # type: ignore[import-not-found]


# WORKSPACE SUBSYSTEM: TEMPLATE SEEDING & FILE SYNCHRONIZATION
# This utility inspects workspace target directories and securely copies missing configuration
# or data files from resolved source paths without overwriting existing user modifications.
# [>] EXECUTING TEMPLATE FILE SEEDING
def seed_files(
    target_dir: Path,
    default_templates_dir: Path,
    files: list[str] | None,
    custom_sources: dict[str, Path | str] | None = None,
) -> None:
    """
    Seeds target directory with template files if the user files do not already exist,
    utilizing resolved default or custom source paths.

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
    # Iterates through target files, copying them from resolved sources only if missing locally.
    for filename in files:
        user_file = target_dir / filename

        # TEMPLATE SOURCE RESOLUTION
        # Resolves the exact source path using custom overrides or default system directories.
        source_file = resolve_template_source(
            filename, default_templates_dir, custom_sources
        )

        # SAFE COPY EXECUTION
        # Copies template source to user workspace if user file does not exist and source is present.
        if not user_file.exists() and source_file.exists():
            shutil.copy(source_file, user_file)
