import shutil
from pathlib import Path
from pathlib import Path


# FOLDER UTILS SUBSYSTEM: PATH & FILTER RESOLUTION
# This utility resolves and filters file and directory paths during directory replication and scanning.
# [>] EXECUTING PATH RESOLUTION & FILTER CHECKS
def should_ignore(path: Path, ignore_patterns: list[str]) -> bool:
    """
    Determines if a given path matches any ignore pattern or filename.

    Args:
        path (Path): The file or directory path to check.
        ignore_patterns (list[str]): List of names, suffixes, or patterns to ignore.

    Returns:
        bool: True if the path should be ignored, False otherwise.
    """
    # EARLY EXIT CHECK: EMPTY PATTERNS
    # Returns False immediately if no ignore patterns or filters are defined.
    if not ignore_patterns:
        return False

    # PATTERN MATCHING EVALUATION
    # Checks if the file or directory name or its file suffix matches any item in the ignore patterns list.
    return path.name in ignore_patterns or path.suffix in ignore_patterns


# FOLDER UTILS SUBSYSTEM: RECURSIVE CLEANING & REMOVAL
# This utility inspects target directories and recursively removes unwanted files or subfolders matching specified targets.
# [>] EXECUTING RECURSIVE REMOVAL
def recursive_remove(
    root_dir: Path | str, targets: list[str], keep_files: list[str] | None = None
) -> None:
    """
    Recursively removes files or folders matching specific names or extensions from a root directory.

    Args:
        root_dir (Path | str): The directory to clean.
        targets (list[str]): List of file/folder names or extensions to remove (e.g., ['.DS_Store', 'temp']).
        keep_files (list[str] | None, optional): List of file or folder names to preserve from deletion.

    Returns:
        None: Executes recursive deletion in-place across the target directory structure.
    """
    # PATH RESOLUTION & EXISTENCE CHECK
    # Converts the root directory input into a Path object and returns early if the path does not exist on the filesystem.
    root_path = Path(root_dir)
    if not root_path.exists():
        return

    # KEEP FILES INITIALIZATION
    # Normalizes the keep_files argument to an empty list if None is provided.
    keep_files = keep_files or []

    # REVERSE ITERATION FOR SAFE DEPTH-FIRST DELETION
    # Iterates in reverse order to ensure files inside directories are removed before parent directories.
    for current_path in sorted(root_path.glob("**/*"), reverse=True):
        # PROTECTED FILE/FOLDER CHECK
        # Skips current path if its name matches any item designated in the keep list.
        if current_path.name in keep_files:
            continue

        # TARGET MATCHING & DELETION DISPATCH
        # Checks if the current path name or suffix matches any designated target pattern,
        # then safely removes directories using rmtree or files using unlink, handling exceptions gracefully.
        if current_path.name in targets or current_path.suffix in targets:
            try:
                if current_path.is_dir():
                    shutil.rmtree(current_path)
                else:
                    current_path.unlink()
            except Exception as e:
                print(f"Failed to remove {current_path}: {e}")


# FOLDER UTILS SUBSYSTEM: FILE CONTENT TRANSFORMATION
# This utility scans target directories for files matching specified extensions
# and applies dictionary-based string replacements across file contents.
# [>] EXECUTING FILE CONTENT TRANSFORMATIONS
def transform_files(
    root_dir: Path | str,
    transform_dict: dict[str, str],
    file_extensions: list[str] | None = None,
    keep_files: list[str] | None = None,
) -> None:
    """
    Scans files and applies replacements based on a provided target dictionary.

    Args:
        root_dir (Path | str): Directory containing files to process.
        transform_dict (dict[str, str]): Dictionary mapping search strings to replacement strings.
        file_extensions (list[str] | None, optional): Optional list of file extensions to target (e.g., ['.py', '.json']).
        keep_files (list[str] | None, optional): List of file names to preserve from content transformation.

    Returns:
        None: Modifies matching files in-place on the filesystem.
    """
    # PATH RESOLUTION & EXISTENCE CHECK
    # Converts the root directory input into a Path object and returns early if the path does not exist on the filesystem.
    root_path = Path(root_dir)
    if not root_path.exists():
        return

    # KEEP FILES INITIALIZATION
    # Normalizes the keep_files argument to an empty list if None is provided.
    keep_files = keep_files or []

    # FILE ITERATION & MODIFICATION SCAN
    # Recursively traverses all files within the root directory path.
    for file_path in root_path.glob("**/*"):
        if file_path.is_file():
            # PROTECTED FILE CHECK
            # Skips files whose name matches any item designated in the keep list.
            if file_path.name in keep_files:
                continue

            # EXTENSION FILTERING CHECK
            # Skips files that do not match the specified target file extensions, if provided.
            if file_extensions and file_path.suffix not in file_extensions:
                continue

            try:
                # CONTENT READING & IN-PLACE MODIFICATION
                # Reads the file text contents using UTF-8 encoding and applies string replacement mappings from the dictionary.
                content = file_path.read_text(encoding="utf-8")
                modified = False

                for search_term, replace_term in transform_dict.items():
                    if search_term in content:
                        content = content.replace(search_term, replace_term)
                        modified = True

                # CONDITIONAL PERSISTENCE COMMITMENT
                # Writes the updated text content back to disk only if modifications occurred.
                if modified:
                    file_path.write_text(content, encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                # EXCEPTION HANDLING: SAFE BYPASS
                # Safely catches decoding or permission errors and continues processing remaining files.
                continue


# FOLDER UTILS SUBSYSTEM: FOLDER REPLICATION & SUBSYSTEM ORCHESTRATION
# CONCRETE CONTROLLER: COPY, CLEAN, AND TRANSFORM DELEGATION
# Orchestrates copying a folder, filtering out unwanted files, cleaning targets recursively,
# and executing content transformations.
# [>] EXECUTING FOLDER REPLICATION & TRANSFORMATION ORCHESTRATION
def copy_and_transform_folder(
    source: Path | str,
    destination: Path | str,
    ignore_patterns: list[str] | None = None,
    remove_targets: list[str] | None = None,
    transform_dict: dict[str, str] | None = None,
    transform_extensions: list[str] | None = None,
    keep_files: list[str] | None = None,
) -> Path:
    """
    Orchestrates directory copying, recursive target removal, and dictionary-based file transformations.

    Args:
        source (Path | str): Source directory path.
        destination (Path | str): Destination directory path.
        ignore_patterns (list[str] | None, optional): Patterns/names to ignore during copy.
        remove_targets (list[str] | None, optional): Files/folders to recursively remove post-copy.
        transform_dict (dict[str, str] | None, optional): Dictionary mapping search terms to replacements.
        transform_extensions (list[str] | None, optional): File extensions to filter for transformations.
        keep_files (list[str] | None, optional): List of file or folder names to preserve from deletion or overwriting.

    Returns:
        Path: The resolved destination path.
    """
    # PATH RESOLUTION & EXISTENCE CHECK
    # Converts source and destination inputs into Path objects and raises FileNotFoundError if the source directory is missing.
    src_path = Path(source)
    dest_path = Path(destination)

    if not src_path.exists():
        raise FileNotFoundError(f"Source directory does not exist: {src_path}")

    # KEEP FILES INITIALIZATION
    # Normalizes the keep_files argument to an empty list if None is provided.
    keep_files = keep_files or []

    # CUSTOM COPY FUNCTION FOR PROTECTED FILES
    # Defines a custom copy wrapper that prevents overwriting any file listed in keep_files if it already exists.
    # copytree passes string paths, so the signature must match shutil's expected callable contract.
    def custom_copy(source: str, destination: str):
        src_p = Path(source)
        dst_p = Path(destination)
        if dst_p.name in keep_files and dst_p.exists():
            return  # Skip copying/overwriting if it's a kept file
        return shutil.copy2(src_p, dst_p)

    # DESTINATION PREPARATION & DIRECTORY CREATION
    # Ensures destination directory exists without blindly wiping out existing kept files.
    dest_path.mkdir(parents=True, exist_ok=True)

    # DIRECTORY COPY DELEGATION
    # Copies the folder tree, merging into destination and respecting keep_files via custom copy function.
    ignore_func = shutil.ignore_patterns(*ignore_patterns) if ignore_patterns else None
    shutil.copytree(
        src_path,
        dest_path,
        ignore=ignore_func,
        dirs_exist_ok=True,
        copy_function=custom_copy,
    )

    # RECURSIVE CLEANING DELEGATION
    # Removes unwanted stray files or folders inside the destination while respecting keep_files.
    if remove_targets:
        recursive_remove(dest_path, remove_targets, keep_files=keep_files)

    # FILE TRANSFORMATION DELEGATION
    # Applies search-and-replace transformations using the provided dictionary while respecting keep_files.
    if transform_dict:
        transform_files(
            dest_path, transform_dict, transform_extensions, keep_files=keep_files
        )

    # DESTINATION PATH RETURN
    # Returns the resolved Path object of the newly replicated and transformed destination directory.
    return dest_path


"""source = Path.home() / "Documents/debian_package/mkv-encode-1.0.0"
destination = Path.home() / "Documents/github/project/mkv-encode-1.0.0"

copy_and_transform_folder(
    source=source,
    destination=destination,
    remove_targets=["__pycache__", ".mypy_cache"],
)"""


"""source = (
    Path.home()
    / "/home/cyril/Documents/debian_package/mkv-encode-1.0.0/usr/lib/mkv-encode/interface/user_input"
)
destination = (
    Path.home()
    / "/home/cyril/Documents/github/python_vault/core/interface/linux/user_input"
)

replacements = {
    "from interface.status_reporter import report_status, LogContext  # type: ignore[import-not-found]": "from status_reporter import report_status, LogContext  # type: ignore[import-not-found]",
    "from security.runtime_pkg import context, log_path  # type: ignore[import-not-found]": "from runtime_pkg import context, log_path  # type: ignore[import-not-found]",
}

copy_and_transform_folder(
    source=source,
    destination=destination,
    transform_dict=replacements,
    transform_extensions=[".py"],
    remove_targets=["__pycache__"],
    keep_files=["README.md"],
)"""


source = (
    Path.home()
    / "/home/cyril/Documents/debian_package/mkv-encode-1.0.0/usr/lib/mkv-encode/interface/status_reporter"
)
destination = (
    Path.home()
    / "/home/cyril/Documents/github/python_vault/core/interface/cross-platform/status_reporter"
)

copy_and_transform_folder(
    source=source,
    destination=destination,
    transform_extensions=[".py"],
    remove_targets=["__pycache__"],
    keep_files=["README.md"],
)
