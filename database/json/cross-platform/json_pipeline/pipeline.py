from typing import Any, Literal, Callable

from .sanitizer import clean_data, sanitize, trace  # type: ignore[import-not-found]
from .query import get_data, get_keys, print_path  # type: ignore[import-not-found]
from .mutation import set_data, append_data, ingest_schema  # type: ignore[import-not-found]
from .persistence import load_from_file, save_to_file  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# PIPELINE MANAGER: JSON-BASED OBJECT-RELATIONAL MAPPING (ORM)
# The JsonPipeline class serves as a structural abstraction layer, transforming raw JSON data into a
# manageable, queryable, and schema-agnostic interface. By decoupling the application logic from the
# underlying file storage, it ensures the script can navigate complex, nested data structures without
# tight coupling to the data's physical format.
class JSONDatabasePipeline:
    """
    Acts as an Object-Relational Mapper (ORM) for JSON.
    Decouples application logic from raw data storage, allowing for
    schema-agnostic access and defensive data retrieval.
    """

    # DATA CONTAINER SUBSYSTEM: CONTAINER INITIALIZATION & PATH BINDING (RE-ENTRY)
    # Re-verifying and documenting the container initialization hook, binding in-memory data structures
    # and establishing file path references for persistent auto-save workflows.
    def __init__(
        self,
        data: dict[str, Any] | list[Any] | None = None,
        file_path: str | None = None,
    ) -> None:
        """
        Initialize the data container with an optional payload and target persistence path.

        Args:
            data (dict[str, Any] | list[Any] | None, optional): Initial in-memory data payload. Defaults to None.
            file_path (str | None, optional): Target file path for persistent writes. Defaults to None.
        """
        # VOLATILE MEMORY CACHE INITIALIZATION
        # Map the incoming data argument to an internal property for high-speed read/write operations,
        # ensuring a consistent data snapshot throughout the object's lifecycle.
        self.data: dict[str, Any] | list[Any] = data if data is not None else {}

        # INTERNAL FILENAME MAPPING & PERSISTENCE BINDING
        # Store the target file path reference to enable targeted write operations and auto-save workflows
        # without requiring explicit path arguments on every save call.
        self.current_path: str | None = file_path

    # DATA CONTAINER SUBSYSTEM: FACTORY CREATION METHOD
    # This class method instantiates a new in-memory pipeline state container. It provides a clean entry point
    # for fresh data structures, logging memory initialization telemetry and pre-mapping the physical disk
    # persistence target to prevent orphaned states.
    @classmethod
    def create(
        cls, initial_state: dict[str, Any] | None = None, file_path: str | None = None
    ) -> "JSONDatabasePipeline":
        """
        Initializes a new Pipeline instance in memory.
        This acts as the starting point for fresh data structures.

        Args:
            initial_state (dict[str, Any] | None, optional): Initial data payload dictionary. Defaults to None.
            file_path (str | None, optional): Target file path for subsequent persistent writes. Defaults to None.

        Returns:
            JSONDatabasePipeline: A newly instantiated pipeline container instance.
        """
        # INITIALIZATION TELEMETRY REPORTING
        # Emit symbolic log statement indicating memory allocation for the new pipeline state
        report_status(
            state="info",
            message="Initializing new pipeline state",
            context=LogContext(
                component="database.JSONDatabasePipeline",
                log_path=log_path,
                silent=False,
                trace_id="JSONDatabasePipeline",
                actor=context.get("user"),
                payload={"file_path": file_path},
            ),
        )

        # CLASS INSTANTIATION & PATH BINDING
        # Return a new instance of the class initialized with default or provided state and file path mapping
        return cls(
            data=initial_state if initial_state is not None else {}, file_path=file_path
        )

    # DATA CONTAINER SUBSYSTEM: DELEGATED FILE LOADER WRAPPER
    # This static method provides a simplified entry point for loading pipeline instances from disk
    # by delegating the ingestion logic to an external utility (`load_from_file`), maintaining modular
    # separation of concerns across the persistence layer.
    @staticmethod
    def from_file(file_path: str) -> "JSONDatabasePipeline":
        """
        Loads a pipeline instance from disk by delegating to a modular file loader utility.

        Args:
            file_path (str): Target filesystem path for the database file.

        Returns:
            JSONDatabasePipeline: The loaded pipeline container instance.
        """
        # PERSISTENCE DELEGATION: EXTERNAL LOADER INVOCATION
        # Delegate the file loading, validation, and parsing logic to the centralized load_from_file utility,
        # passing the pipeline class reference and target path.
        return load_from_file(JSONDatabasePipeline, file_path)

    # DATA CONTAINER SUBSYSTEM: DELEGATED DATA PRUNING WRAPPER
    # This internal method provides a clean wrapper for recursive data pruning by delegating
    # the sanitization logic to an external utility (`clean_data`), maintaining modular separation
    # of concerns across the persistence layer.
    def _clean_data(self, object: Any) -> Any:
        """
        Sanitizes data payloads by delegating to a modular data cleaning utility.

        Args:
            object (Any): The data object to be sanitized.

        Returns:
            Any: The cleaned and pruned data structure.
        """
        # PERSISTENCE DELEGATION: EXTERNAL CLEANER INVOCATION
        # Delegate the recursive pruning and metadata stripping logic to the centralized clean_data utility.
        return clean_data(object)

    # DATA CONTAINER SUBSYSTEM: DELEGATED PATH SANITIZATION WRAPPER
    # This internal method provides a clean wrapper for path tokenization and normalization
    # by delegating the grammar processing logic to an external utility (`sanitize`),
    # maintaining modular separation of concerns across the persistence layer.
    def _sanitize(self, path: str) -> list[str]:
        """
        Tokenizes and normalizes path protocols by delegating to a modular sanitization utility.

        Args:
            path (str): The raw string path to tokenize.

        Returns:
            list[str]: A sequence of clean navigational tokens representing targeted nodes.
        """
        # PERSISTENCE DELEGATION: EXTERNAL SANITIZER INVOCATION
        # Delegate path normalization, bracket-to-dot conversion, and void filtering to the centralized sanitize utility.
        return sanitize(path)

    # DATA CONTAINER SUBSYSTEM: DELEGATED PATH DECONSTRUCTION WRAPPER
    # This internal method provides a clean wrapper for recursive path deconstruction and identity promotion
    # by delegating the path unrolling logic to an external utility (`trace`), maintaining modular separation
    # of concerns across the persistence layer.
    def _trace(self, data: Any, current_path: str = "") -> list[tuple[str, Any]]:
        """
        Unrolls nested data structures into flat (Path, Value) tuples by delegating to a modular trace utility.

        Args:
            data (Any): The data node to deconstruct.
            current_path (str, optional): The accumulated path string from parent nodes. Defaults to "".

        Returns:
            list[tuple[str, Any]]: A flat list of resolved dot-predicate paths and their leaf values.
        """
        # PERSISTENCE DELEGATION: EXTERNAL TRACE INVOCATION
        # Delegate the recursive path deconstruction and identity promotion logic to the centralized trace utility.
        return trace(data, current_path)

    # DATA CONTAINER SUBSYSTEM: DELEGATED DATA RETRIEVAL WRAPPER
    # This method provides a clean wrapper for fetching deeply nested data by delegating
    # the query logic to an external utility (`get_data`), maintaining modular separation
    # of concerns across the persistence layer.
    def get_data(self, path: str) -> Any | None:
        """
        Retrieves data using a normalized path protocol by delegating to a modular data retrieval utility.

        Args:
            path (str): The target dot-notation or predicate query path.

        Returns:
            Any | None: The resolved data value, or None if the path does not exist.
        """
        # PERSISTENCE DELEGATION: EXTERNAL GET_DATA INVOCATION
        # Delegate the tokenized traversal and predicate matching logic to the centralized get_data utility,
        # passing the internal data state and target path.
        return get_data(self.data, path)

    # DATA CONTAINER SUBSYSTEM: DELEGATED DIAGNOSTIC INTERFACE WRAPPER
    # This method provides a clean wrapper for the high-level CLI diagnostic inspector by delegating
    # the inspection, type-safe dispatch, and rendering logic to an external utility (`print_path`),
    # maintaining modular separation of concerns across the persistence layer.
    def print_path(
        self,
        path: str,
        view: (
            Literal["flat", "json"]
            | dict[str, str]
            | Callable[[Any, list[str], str], None]
        ) = "flat",
    ) -> None:
        """
        High-level CLI inspector by delegating to a modular print utility.

        Args:
            path (str): Dot-notated string targeting specific nodes within the internal state.
            view (Literal["flat", "json"] | dict[str, str] | Callable[[Any, list[str], str], None], optional):
                Output format control, view configuration schema, or a custom render callable. Defaults to "flat".
        """
        # PERSISTENCE DELEGATION: EXTERNAL PRINT_PATH INVOCATION
        # Delegate path resolution, metadata pruning, strategy resolution, and framed terminal
        # rendering to the centralized print_path utility, passing the pipeline instance data,
        # target path, and view configuration or custom renderer callable.
        print_path(self.data, path, view)

    # DATA CONTAINER SUBSYSTEM: DELEGATED EXPLORATION API WRAPPER
    # This method provides a clean wrapper for the schema exploration API by delegating
    # the key extraction and documentation filtering logic to an external utility (`get_keys`),
    # maintaining modular separation of concerns across the persistence layer.
    def get_keys(self, path: str = "") -> list[str]:
        """
        Retrieves a list of functional keys at a specified path by delegating to a modular exploration utility.

        Args:
            path (str, optional): The starting node path for exploration. Defaults to "" (root).

        Returns:
            list[str]: A list of non-documentation functional keys residing at the target node.
        """
        # PERSISTENCE DELEGATION: EXTERNAL GET_KEYS INVOCATION
        # Delegate schema exploration, key extraction, and '//_' documentation filtering
        # to the centralized get_keys utility, passing the internal data state and path.
        return get_keys(self.data, path)

    # DATA CONTAINER SUBSYSTEM: DELEGATED DATA MUTATION WRAPPER
    # This method provides a clean wrapper for updating or inserting deeply nested data by delegating
    # the mutation logic to an external utility (`set_data`), maintaining modular separation
    # of concerns across the persistence layer with optional automatic path creation.
    def set_data(self, path: str, value: Any, auto_create: bool = True) -> bool:
        """
        Updates or sets data using a normalized path protocol by delegating to a modular data mutation utility.

        Args:
            path (str): The target dot-notation or predicate query path for the mutation.
            value (Any): The value to assign at the target location.
            auto_create (bool, optional): Whether to automatically create missing intermediate nodes. Defaults to True.

        Returns:
            bool: True if the mutation was successful, False otherwise.
        """
        # PERSISTENCE DELEGATION: EXTERNAL SET_DATA INVOCATION
        # Delegate the tokenized traversal, assignment, and optional auto-creation logic
        # to the centralized set_data utility, passing the internal data state, path, value, and flags.
        return set_data(self.data, path, value, auto_create=auto_create)

    # DATA CONTAINER SUBSYSTEM: DELEGATED SCHEMA INGESTION WRAPPER
    # This method provides a clean wrapper for schema-driven data ingestion by delegating
    # the validation and insertion logic to an external utility (`ingest_schema`), maintaining modular
    # separation of concerns across the persistence layer.
    def ingest_schema(
        self,
        inputs: dict[str, Any],
        custom_key: str,
        schema: dict[str, Any] | None = None,
    ) -> bool:
        """
        Ingests and validates input data against a schema by delegating to a modular ingestion utility.

        Args:
            inputs (dict[str, Any]): The raw input dictionary to ingest.
            custom_key (str): The target destination key or path within the pipeline state.
            schema (dict[str, Any] | None, optional): Optional validation schema for the input data. Defaults to None.

        Returns:
            bool: True if ingestion and validation succeed, False otherwise.
        """
        # PERSISTENCE DELEGATION: EXTERNAL INGEST_SCHEMA INVOCATION
        # Delegate schema validation, input parsing, and state assignment logic
        # to the centralized ingest_schema utility, passing the pipeline instance, inputs, key, and schema.
        return ingest_schema(self.data, inputs, custom_key, schema=schema)

    # DATA CONTAINER SUBSYSTEM: DELEGATED DATA APPEND WRAPPER
    # This method provides a clean wrapper for appending new entries to sequence-based data nodes
    # by delegating the append logic to an external utility (`append_data`), supporting optional
    # uniqueness checking and automatic path creation.
    def append_data(
        self, path: str, new_entry: Any, unique: bool = False, auto_create: bool = True
    ) -> bool:
        """
        Appends a new entry to a list node by delegating to a modular append utility.

        Args:
            path (str): The target dot-notation or predicate query path pointing to a list node.
            new_entry (Any): The item to append to the target sequence.
            unique (bool, optional): Whether to enforce uniqueness (prevent duplicates). Defaults to False.
            auto_create (bool, optional): Whether to automatically create intermediate nodes or lists if missing. Defaults to True.

        Returns:
            bool: True if the append operation was successful, False otherwise.
        """
        # PERSISTENCE DELEGATION: EXTERNAL APPEND_DATA INVOCATION
        # Delegate the sequence targeting, uniqueness verification, and list extension logic
        # to the centralized append_data utility, passing the pipeline instance, path, entry, and flags.
        return append_data(self.data, path, new_entry, unique, auto_create)

    # DATA CONTAINER SUBSYSTEM: DELEGATED PERSISTENCE SAVE WRAPPER
    # This method provides a clean wrapper for persisting pipeline state to disk by delegating
    # the serialization, file writing, and backup management logic to an external utility (`save_to_file`),
    # ensuring data safety, atomic updates, and rolling backup rotation.
    def save(
        self,
        file_path: str | None = None,
        backup: bool = False,
        max_backups: int = 3,
    ) -> bool:
        """
        Persists the current pipeline state to disk by delegating to a modular save utility.

        Args:
            file_path (str | None, optional): Target filesystem path for saving. Defaults to current path if None.
            backup (bool, optional): Whether to create a rolling backup before overwriting. Defaults to False.
            max_backups (int, optional): Maximum number of backup files to retain. Defaults to 3.

        Returns:
            bool: True if the save and serialization operation succeeded, False otherwise.
        """
        # PERSISTENCE DELEGATION: EXTERNAL SAVE_TO_FILE INVOCATION
        # Delegate state serialization, atomic file writing, and backup rotation
        # to the centralized save_to_file utility, passing internal data, current path, and parameters.
        return save_to_file(
            self.data,
            self.current_path,
            file_path=file_path,
            backup=backup,
            max_backups=max_backups,
        )
