from pathlib import Path


# ARCHITECTURAL PATH MAPPER: DYNAMIC WORKSPACE ROUTING ENGINE
# This function generates a predictable, isolated dictionary of directory and file paths
# relative to a base directory and runtime scope identifier.
# It acts as a logical path planner, decoupling application layout definition from physical provisioning.
def generate_workspace_paths(
    base_dir: str | Path,
    scope: str,
    subdirectories: list[str] | None = None,
    files: list[str] | None = None,
) -> dict[str, Path]:
    """Generates a structured mapping of directory and file paths relative to a

    base directory and a dynamic scope (e.g., user, environment, or project
    ID).

    Args:
        base_dir (str | Path): Root storage path (e.g., "/app/data").
        scope (str): Dynamic identifier used for isolation (e.g., username,
          project_id, env).
        subdirectories (list[str] | None): Optional list of folder names to construct under the
          scoped directory.
        files (list[str] | None): Optional list of file names to construct under the scoped
          directory.

    Returns:
        Dict mapping keys (in UPPERCASE) to their resolved pathlib.Path objects.
    """
    # ROOT & SCOPE RESOLUTION PASS
    # Initializes root storage target and constructs the isolated scoped directory path container.
    root_path = Path(base_dir)
    scope_dir = root_path / scope

    # BASE REGISTRY DICTIONARY INITIALIZATION
    # Seeds the path mapping dictionary with foundational base and scope references.
    paths: dict[str, Path] = {
        "BASE_DIR": root_path,
        "SCOPE_DIR": scope_dir,
    }

    # CUSTOM SUBDIRECTORY NORMALIZATION & KEY MAPPING
    # Iterates through optional subdirectory specifications, sanitizing keys for clean uppercase dictionary storage.
    if subdirectories:
        for sub_dir in subdirectories:
            # SANITIZATION PASS: STRIP LEADING PATH DELIMITERS
            # Clean leading dots and slashes to ensure consistent key naming conventions.
            clean_key = sub_dir.lstrip("./").upper().replace("/", "_")

            # ABSOLUTE PATH RESOLUTION MAPPING
            # Binds the normalized uppercase dictionary key to the evaluated pathlib composite route.
            paths[clean_key] = scope_dir / sub_dir

    # CUSTOM FILE NORMALIZATION & KEY MAPPING
    # Iterates through optional file specifications, stripping extensions and formatting keys for uniform access.
    if files:
        for file_name in files:
            # SANITIZATION PASS: STRIP EXTENSIONS & LEADING CHARACTERS
            # Isolate base filename tokens by discarding leading dots and trailing file extensions.
            clean_key = file_name.lstrip(".").split(".")[0].upper()

            # TARGET FILE PATH BINDING
            # Assigns the resolved file path reference back into the path routing catalog.
            paths[clean_key] = scope_dir / file_name

    # REGISTRY RETURN PIPELINE
    # Returns the fully constructed and normalized path mapping catalog.
    return paths
