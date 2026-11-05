import json
import os
import shutil
from typing import Any

from .constants import report_status, LogContext, user_input, context, log_path  # type: ignore[import-not-found]


# DATA PERSISTENCE SUBSYSTEM: FILE INGESTION & PIPELINE INITIALIZATION
# This utility loads persisted JSON data snapshots from disk, manages file-not-found warnings,
# prompts the operator for database initialization consent, and handles JSON decoding corruption errors.
# [>] EXECUTING FILE INGESTION & PIPELINE LOADING
def load_from_file(pipeline_cls: Any, file_path: str) -> Any:
    """
    Loads a JSON file or prompts the user to initialize a new one.

    Args:
        pipeline_cls (Any): The pipeline class constructor to instantiate.
        file_path (str): The target file path on disk to ingest or initialize.

    Returns:
        Any: The instantiated pipeline instance populated with data or created empty.
    """
    # FILE EXISTENCE VERIFICATION & WARNING REPORTING
    # Checks if the target data file exists on disk, logging a warning and triggering
    # initialization workflows if the source path is missing.
    if not os.path.exists(file_path):
        report_status(
            state="warn",
            message=f"Source file not found: {file_path!r}",
            context=LogContext(
                component="database.JSONDatabasePipeline",
                log_path=log_path,
                silent=False,
                trace_id="JSONDatabasePipeline",
                actor=context.get("user"),
                payload={"file_path": file_path},
            ),
        )
        choice_schema: list[dict[str, Any]] = [
            {
                "key": "user_consent",
                "label": "Initialize a new database at this location",
                "cast": "bool",
                "default": True,
            }
        ]
        choice = user_input(schema=choice_schema, silent=True)

        # USER CONSENT EVALUATION & PIPELINE CREATION
        # Evaluates the operator's initialization consent, instantiating a new pipeline
        # at the target path if approved, or returning an unlinked empty pipeline upon cancellation.
        if choice.get("user_consent"):
            report_status(
                state="info",
                message=f"Initializing new pipeline for {file_path!r}",
                context=LogContext(
                    component="database.JSONDatabasePipeline",
                    log_path=log_path,
                    silent=False,
                    trace_id="JSONDatabasePipeline",
                    actor=context.get("user"),
                    payload={"file_path": file_path},
                ),
            )
            return pipeline_cls.create(file_path=file_path)
        else:
            report_status(
                state="warn",
                message="Operation cancelled. Returning empty state.",
                context=LogContext(
                    component="database.JSONDatabasePipeline",
                    log_path=log_path,
                    silent=False,
                    trace_id="JSONDatabasePipeline",
                    actor=context.get("user"),
                    payload={"file_path": file_path},
                ),
            )
            return pipeline_cls.create()

    # FILE INGESTION & JSON DECODING
    # Attempts to open, read, and decode the persisted JSON snapshot from disk,
    # logging success and returning an instantiated pipeline populated with the loaded data.
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            report_status(
                state="info",
                message=f"Ingested data snapshot: {file_path!r}",
                context=LogContext(
                    component="database.JSONDatabasePipeline",
                    log_path=log_path,
                    silent=True,
                    trace_id="JSONDatabasePipeline",
                    actor=context.get("user"),
                    payload={"file_path": file_path},
                ),
            )
            data = json.load(f)
            return pipeline_cls(data, file_path=file_path)

    # JSON DECODING CORRUPTION HANDLING
    # Captures malformed JSON decoding errors, logs failure status, and falls back
    # to initializing a fresh pipeline instance at the target file path.
    except json.JSONDecodeError as e:
        report_status(
            state="fail",
            message=f"Source data corrupted: {e}",
            context=LogContext(
                component="database.JSONDatabasePipeline",
                log_path=log_path,
                silent=False,
                trace_id="JSONDatabasePipeline",
                actor=context.get("user"),
                exception=str(e),
                payload={"file_path": file_path},
            ),
        )
        return pipeline_cls.create(file_path=file_path)


# DATA PERSISTENCE SUBSYSTEM: SERIALIZATION & BACKUP ROTATION ENGINE
# This utility persists the current state of data containers back to disk with automated backup file rotation,
# destination path validation, formatted JSON dumping, and robust I/O error handling.
# [>] EXECUTING FILE PERSISTENCE & BACKUP ROTATION
def save_to_file(
    data: Any,
    current_path: str | None,
    file_path: str | None = None,
    backup: bool = False,
    max_backups: int = 3,
) -> bool:
    """
    Persists the current state of the database back to disk with backup rotation.

    Args:
        data (Any): The data container or state object to serialize and save.
        current_path (str | None): The default pipeline persistence path.
        file_path (str | None, optional): Explicit target override path for saving. Defaults to None.
        backup (bool, optional): Boolean flag enabling automated backup rotation prior to saving. Defaults to False.
        max_backups (int, optional): Maximum number of backup file generations to retain. Defaults to 3.

    Returns:
        bool: True if the file was successfully persisted; False otherwise.
    """
    # TARGET PATH RESOLUTION & VALIDATION
    # Determines the active persistence target path from explicit arguments or pipeline state,
    # reporting a failure status and returning False if no destination is assigned.
    target: str | None = file_path or current_path
    if not target:
        report_status(
            state="fail",
            message="No destination path assigned to pipeline.",
            context=LogContext(
                component="database.JSONDatabasePipeline",
                log_path=log_path,
                silent=False,
                trace_id="JSONDatabasePipeline",
                actor=context.get("user"),
                payload={"current_path": current_path, "file_path": file_path},
            ),
        )
        return False

    # BACKUP ROTATION & FILE SHIFTING
    # Shifts existing backup file generations upwards and copies the current target file to `.bak1`
    # prior to overwriting, capturing and reporting any file system rotation errors.
    if backup and os.path.exists(target):
        try:
            for i in range(max_backups - 1, 0, -1):
                old_bak: str = f"{target}.bak{i}"
                new_bak: str = f"{target}.bak{i+1}"
                if os.path.exists(old_bak):
                    os.replace(old_bak, new_bak)
            shutil.copy2(target, f"{target}.bak1")
        except OSError as e:
            report_status(
                state="fail",
                message=f"Error rotating backup files: {e}",
                context=LogContext(
                    component="database.JSONDatabasePipeline",
                    log_path=log_path,
                    silent=False,
                    trace_id="JSONDatabasePipeline",
                    actor=context.get("user"),
                    exception=str(e),
                    payload={"target": target, "max_backups": max_backups},
                ),
            )

    # JSON SERIALIZATION & DISK PERSISTENCE
    # Attempts to serialize and write the data payload formatted with indentation to disk,
    # returning True on success or reporting I/O errors and returning False on failure.
    try:
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        report_status(
            state="fail",
            message=f"Error saving to file: {e}",
            context=LogContext(
                component="database.JSONDatabasePipeline",
                log_path=log_path,
                silent=False,
                trace_id="JSONDatabasePipeline",
                actor=context.get("user"),
                exception=str(e),
                payload={"target": target},
            ),
        )
        return False
