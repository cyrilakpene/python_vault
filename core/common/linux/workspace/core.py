from pathlib import Path

from .paths import resolve_workspace_paths  # type: ignore[import-not-found]
from .seeder import seed_files  # type: ignore[import-not-found]


# WORKSPACE SUBSYSTEM: WORKSPACE INITIALIZATION & SUBSYSTEM ORCHESTRATION
# CONCRETE CONTROLLER: PATH RESOLUTION & FILE SEEDING DELEGATION
# Orchestrates user workspace initialization by resolving XDG paths, ensuring directory
# existence, and delegating template configuration seeding to modular subsystems with custom source support.
def initialize_user_workspace(
    app_name: str,
    config_files: list[str] | None = None,
    data_files: list[str] | None = None,
    system_template_base: Path | str | None = None,
    template_sources: dict[str, Path | str] | None = None,
) -> tuple[Path, Path]:
    """
    Orchestrates user workspace initialization by resolving paths, ensuring directory
    existence, and seeding template configurations from system or custom sources.

    Args:
        app_name (str): The unique application name.
        config_files (list[str], optional): Configuration filenames to seed.
        data_files (list[str], optional): Data filenames to seed.
        system_template_base (Path | str, optional): Custom system template base path.
        template_sources (dict[str, Path | str], optional): Explicit filename-to-source mapping dictionary.

    Returns:
        tuple[Path, Path]: The resolved config_dir and data_dir paths.
    """
    # PATH RESOLUTION DELEGATION
    # Resolves configuration, data, and system template paths via the paths subsystem.
    config_dir, data_dir, default_templates_dir = resolve_workspace_paths(
        app_name, system_template_base
    )

    # WORKSPACE DIRECTORY INITIALIZATION
    # Ensures user configuration and data directories exist on disk.
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # SEEDING DELEGATION: CONFIGURATION & DATA ARTIFACTS
    # Delegates file seeding routines to the seeder subsystem, passing optional custom source mappings.
    seed_files(config_dir, default_templates_dir, config_files, template_sources)
    seed_files(data_dir, default_templates_dir, data_files, template_sources)

    # FULL FILE PATH RESOLUTION
    # Construct direct paths to the primary files if they were specified in the lists
    config_file_path = (
        config_dir / config_files[0]
        if config_files and len(config_files) > 0
        else config_dir
    )
    data_file_path = (
        data_dir / data_files[0] if data_files and len(data_files) > 0 else data_dir
    )

    # WORKSPACE INITIALIZATION RETURN
    # Returns the resolved full file paths instead of just the root directories
    return config_file_path, data_file_path
