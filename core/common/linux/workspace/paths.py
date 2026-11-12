from pathlib import Path


# WORKSPACE SUBSYSTEM: XDG PATH RESOLUTION & DIRECTORY MAPPING
# This utility resolves XDG-compliant configuration directories (~/.config), local data
# directories (~/.local/share), and system template base paths for application bootstrapping.
# [>] EXECUTING WORKSPACE PATH RESOLUTION
def resolve_workspace_paths(
    app_name: str, system_template_base: str | Path | None = None
) -> tuple[Path, Path, Path]:
    """
    Resolves configuration, data, and system template paths for the application.

    Args:
        app_name (str): The unique application identifier.
        system_template_base (str | Path, optional): Custom base path for system templates.

    Returns:
        tuple[Path, Path, Path]: Resolved config_dir, data_dir, and templates_dir paths.
    """
    # XDG BASE DIRECTORY RESOLUTION
    # Computes standard user config and data paths based on the provided application name.
    config_dir = Path.home() / ".config" / app_name
    data_dir = Path.home() / ".local" / "share" / app_name

    # TEMPLATE DIRECTORY RESOLUTION
    # Resolves the system template directory, falling back to standard system paths if unconstrained.
    templates_dir = (
        Path(system_template_base)
        if system_template_base
        else Path(f"/usr/share/{app_name}/templates")
    )

    # RESOLVED PATHS TUPLE RETURN
    # Returns the configuration, data, and template directories.
    return config_dir, data_dir, templates_dir


# WORKSPACE SUBSYSTEM: TEMPLATE SOURCE RESOLUTION
# This utility resolves explicit source paths for individual template files,
# checking custom override mappings first before falling back to default system directories.
# [>] EXECUTING TEMPLATE SOURCE RESOLUTION
def resolve_template_source(
    filename: str,
    default_templates_dir: Path,
    custom_sources: dict[str, Path | str] | None = None,
) -> Path:
    """
    Resolves the exact source path for a given template file.

    Args:
        filename (str): The filename of the template being resolved.
        default_templates_dir (Path): The fallback system template directory.
        custom_sources (dict[str, Path | str], optional): Explicit filename-to-source mapping dictionary.

    Returns:
        Path: The resolved source file path.
    """
    # CUSTOM SOURCE MAPPING EVALUATION
    # Checks if an explicit custom source path is registered for the specific file.
    if custom_sources and filename in custom_sources:
        return Path(custom_sources[filename])

    # DEFAULT TEMPLATE PATH FALLBACK
    # Falls back to the default system template directory path.
    return default_templates_dir / filename
