from typing import Any, cast

from .sanitizer import sanitize, resolve_branch  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: PATH-BASED DATA MUTATION & DYNAMIC BRANCH INGRESTION
# This utility updates or inserts values at specified tokenized paths within nested data structures,
# supporting dynamic branch auto-creation, list padding, type safety checks, and failure reporting.
# [>] EXECUTING PATH-BASED DATA MUTATION
def set_data(
    data_root: dict[str, Any] | list[Any],
    path: str,
    value: Any,
    auto_create: bool = True,
) -> bool:
    """
    Updates a value at the specified path, supporting dynamic lists.

    Args:
        data_root (dict[str, Any] | list[Any]): The root data container to mutate.
        path (str): The target dot-notation or predicate query path.
        value (Any): The value to assign to the target node.
        auto_create (bool, optional): Automatically instantiate missing parent branches or lists. Defaults to True.

    Returns:
        bool: True if the value was successfully set; False on path breaches or type conflicts.
    """
    # INBOUND PATH TOKENIZATION
    # Transforms the target string path into sequential navigational tokens via the grammar engine.
    keys: list[str] = sanitize(path)
    target: Any = data_root

    # INTERMEDIATE NODE TRAVERSAL & BRANCH RESOLUTION
    # Iterates through all parent keys except the terminal node, verifying existence
    # and dynamically creating missing branches or padding lists if auto_create is enabled.
    for i, key in enumerate(keys[:-1]):
        next_key: str = keys[i + 1]
        is_dict_missing: bool = isinstance(target, dict) and key not in target
        is_list_out_of_bounds: bool = (
            isinstance(target, list)
            and key.isdigit()
            and int(key) >= len(cast(list[Any], target))
        )

        # AUTOMATIC BRANCH & LIST PADDING CREATION
        # Instantiates missing dictionaries or lists (or pads list indices with None)
        # when structural gaps are encountered and auto_create is active.
        if is_dict_missing or is_list_out_of_bounds:
            if auto_create:
                new_branch: dict[str, Any] | list[Any] = (
                    [] if next_key.isdigit() else {}
                )
                if isinstance(target, dict):
                    target[key] = new_branch
                elif isinstance(target, list) and key.isdigit():
                    idx: int = int(key)
                    list_target: list[Any] = cast(list[Any], target)
                    while len(list_target) <= idx:
                        list_target.append(None)
                    list_target[idx] = new_branch
            else:
                report_status(
                    state="warn",
                    message=f"Path breach at '{'.'.join(keys[:i + 1])}'",
                    context=LogContext(
                        component="database.JSONDatabasePipeline",
                        log_path=log_path,
                        silent=False,
                        trace_id="JSONDatabasePipeline",
                        actor=context.get("user"),
                        payload={"path": path, "breach_key": ".".join(keys[: i + 1])},
                    ),
                )
                return False

        # TRAVERSAL NAVIGATION & TYPE VALIDATION
        # Advances the active target pointer down the tree branch, returning False
        # if type conflicts or invalid indexing attempts occur.
        if isinstance(target, dict):
            target = cast(dict[str, Any], target)[key]
        elif isinstance(target, list) and key.isdigit():
            idx = int(key)
            indexed_list: list[Any] = cast(list[Any], target)
            if idx < len(indexed_list):
                target = indexed_list[idx]
            else:
                return False
        else:
            report_status(
                state="warn",
                message=f"Type conflict: Node {key!r} is a primitive.",
                context=LogContext(
                    component="database.JSONDatabasePipeline",
                    log_path=log_path,
                    silent=False,
                    trace_id="JSONDatabasePipeline",
                    actor=context.get("user"),
                    payload={"path": path, "node_key": key},
                ),
            )
            return False

    # TERMINAL NODE KEY ASSIGNMENT
    # Assigns the target value to the final key, supporting dictionary insertion
    # and automatic bounds padding for list indices.
    last_key: str = keys[-1]
    if isinstance(target, dict):
        target[last_key] = value
        return True
    elif isinstance(target, list) and last_key.isdigit():
        idx = int(last_key)
        final_list_target: list[Any] = cast(list[Any], target)
        while len(final_list_target) <= idx:
            final_list_target.append(None)
        final_list_target[idx] = value
        return True
    return False


# DATA CONTAINER SUBSYSTEM: SEQUENCE MUTATION & LIST APPEND ENGINE
# This utility appends new entries to lists located at tokenized paths within data containers,
# featuring automatic list initialization for missing nodes and optional uniqueness deduplication.
# [>] EXECUTING SEQUENCE APPEND & DEDUPLICATION
def append_data(
    pipeline_instance: Any,
    path: str,
    new_entry: Any,
    unique: bool = False,
    auto_create: bool = True,
) -> bool:
    """
    Appends an object to a list found at the specified path.

    Args:
        pipeline_instance (Any): The data pipeline container instance providing query and mutation access.
        path (str): The dot-notated string path targeting the destination list.
        new_entry (Any): The data object to append into the target sequence.
        unique (bool, optional): Enforce unique entries by skipping appends if the item already exists. Defaults to False.
        auto_create (bool, optional): Automatically initialize an empty list if the target path is missing. Defaults to True.

    Returns:
        bool: True if the entry was successfully appended or already present (when unique=True); False otherwise.
    """
    # TARGET ACQUISITION & AUTOMATIC LIST INITIALIZATION
    # Queries the target node from the pipeline instance, instantiating an empty list
    # at the specified path if the node is missing and auto_create is enabled.
    target: Any = pipeline_instance.get_data(path)
    if target is None and auto_create:
        pipeline_instance.set_data(path, [])
        target = pipeline_instance.get_data(path)

    # SEQUENCE VALIDATION & UNIQUENESS DEDUPLICATION
    # Verifies that the resolved target is a valid list container. If unique is active and
    # the entry already exists within the sequence, bypasses insertion and returns success.
    if isinstance(target, list):
        list_target: list[Any] = cast(list[Any], target)
        if unique and new_entry in list_target:
            return True

        # APPEND EXECUTION
        # Appends the new data entry to the verified sequence container.
        list_target.append(new_entry)
        return True

    # TYPE CONFLICT REPORTING & FAILURE HANDLING
    # Reports a warning status and returns False if the targeted path resolves to a non-list node.
    report_status(
        state="warn",
        message=f"Path {path!r} is not a list.",
        context=LogContext(
            component="database.JSONDatabasePipeline",
            log_path=log_path,
            silent=False,
            trace_id="JSONDatabasePipeline",
            actor=context.get("user"),
            payload={"path": path},
        ),
    )
    return False


# DATA CONTAINER SUBSYSTEM: MULTIMODAL SCHEMA INGESTION & TEMPLATE RESOLUTION
# This utility ingests raw input dictionaries, resolves them against optional schemas or dynamic templates,
# formats the storage key using string interpolation, and persists the payload into the pipeline data container.
# [>] EXECUTING SCHEMA INGESTION & RESOLUTION
def ingest_schema(
    pipeline_instance: Any,
    inputs: dict[str, Any],
    custom_key: str,
    schema: dict[str, Any] | None = None,
) -> bool:
    """
    Multimodal schema ingestion engine.

    Ingests raw inputs, resolves them against a schema template if provided, formats dynamic
    storage keys via string interpolation, and persists the payload into the data pipeline.

    Args:
        pipeline_instance (Any): The target data pipeline instance managing persistence.
        inputs (dict[str, Any]): The raw source input dictionary containing data values.
        custom_key (str): The storage key or template string (e.g., 'user_{id}') for the ingested payload.
        schema (dict[str, Any] | None, optional): Optional structural schema template to resolve inputs against. Defaults to None.

    Returns:
        bool: True if the schema payload was successfully ingested and stored; False on validation or key errors.
    """
    # INPUT VALIDATION & NON-EMPTY CHECK
    # Verifies that the input data dictionary is non-empty, reporting failure and returning False if invalid.
    if not inputs:
        report_status(
            state="fail",
            message="INGESTION FAILURE: 'Inputs' must be a non-empty dictionary.",
            context=LogContext(
                component="database.JSONDatabasePipeline",
                log_path=log_path,
                silent=False,
                trace_id="JSONDatabasePipeline",
                actor=context.get("user"),
                payload={"custom_key": custom_key},
            ),
        )
        return False

    # SCHEMA RESOLUTION OR RAW PASS-THROUGH
    # Resolves the input dictionary against a template schema if provided, or accepts the raw inputs directly.
    if schema is not None:
        content: dict[str, Any] = resolve_branch(schema, inputs)
    else:
        content = inputs

    # KEY FORMATTING & DYNAMIC TEMPLATE INTERPOLATION
    # Evaluates custom keys for template placeholders, formatting them with input values,
    # normalizing case/spaces, and falling back to a default identity on missing keys.
    final_key: str = custom_key
    if "{" in custom_key and "}" in custom_key:
        try:
            final_key = custom_key.format(**inputs).lower().replace(" ", "_")
        except KeyError as e:
            report_status(
                state="fail",
                message=f"Schema ingestion failed due to missing template key: {e}",
                context=LogContext(
                    component="database.JSONDatabasePipeline",
                    log_path=log_path,
                    silent=False,
                    trace_id="JSONDatabasePipeline",
                    actor=context.get("user"),
                    exception=str(e),
                    payload={"custom_key": custom_key},
                ),
            )
            final_key = "generated_identity"

    # PIPELINE PERSISTENCE & STORAGE
    # Stores the resolved content payload under the finalized key within the pipeline instance.
    return pipeline_instance.set_data(final_key, content)
