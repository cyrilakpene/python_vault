from typing import TypeVar, Generic, cast

from .operations import (
    register_item,  # type: ignore[import-not-found]
    register_bulk_items,  # type: ignore[import-not-found]
    get_item,  # type: ignore[import-not-found]
    get_namespace_dict,  # type: ignore[import-not-found]
    dump_storage,  # type: ignore[import-not-found]
)

# TYPING SUBSYSTEM: GENERIC TYPE VARIABLE DEFINITION
# This utility defines a generic type variable T for use in generic class, function,
# and method type annotations across the type-safe architectural subsystems.
# [>] EXECUTING TYPE VARIABLE DEFINITION
T = TypeVar("T")
V = TypeVar("V")


# MULTI-NAMESPACE RUNTIME STORAGE & FUNCTIONAL DELEGATION ENGINE
# CONCRETE REGISTRY: TYPE-BOUNDED DICTIONARY & COMPONENT REPOSITORY
# Implements a multi-namespace runtime storage registry with functional delegation capabilities.
# By decoupling component registration from execution lookups, it guarantees type safety, isolated
# scope namespaces, and rapid retrieval across dynamic module and plugin architectures.
class GenericRegistry(Generic[T]):
    """A multi-namespace runtime storage registry with functional delegation.

    Provides generic type-safe component mapping, namespace isolation, and dynamic callable
    delegation, ensuring clean separation of concerns and extensible storage management across modules.
    """

    # PERSISTENCE & STORAGE SUBSYSTEM: CONTAINER INITIALIZATION
    # This initializer sets up the in-memory or transactional storage container,
    # provisioning a nested dictionary mapping structure to organize records by category and key.
    def __init__(self) -> None:
        """
        Initializes the storage container with an empty nested dictionary mapping.
        """
        # STORAGE STRUCTURE INITIALIZATION
        # Initialize the private storage dictionary with generic type parameters for structured data persistence.
        self._storage: dict[str, dict[str, T]] = {}

    # PERSISTENCE & STORAGE SUBSYSTEM: ITEM REGISTRATION
    # This method registers a single item into a specified namespace within the internal storage container
    # by delegating to an external registration utility, ensuring proper dictionary mapping.
    def register(self, namespace: str, key: str, value: T) -> None:
        """
        Register a single item in a specific namespace.

        Args:
            namespace (str): The target storage namespace or category where the item will be registered.
            key (str): The unique identifier key for the item within the namespace.
            value (T): The value object being registered and stored.
        """
        # REGISTRATION DELEGATION: EXTERNAL REGISTER_ITEM INVOCATION
        # Delegate item insertion, namespace verification, and storage mapping
        # to the centralized register_item utility, passing the private storage structure, namespace, key, and value.
        register_item(self._storage, namespace, key, value)

    # PERSISTENCE & STORAGE SUBSYSTEM: BULK ITEM REGISTRATION
    # This method registers multiple items in bulk within a specific namespace inside the internal storage container
    # by delegating to an external bulk registration utility, ensuring efficient batch dictionary updating.
    def register_bulk(self, namespace: str, items: dict[str, T]) -> None:
        """
        Register multiple items in bulk within a specific namespace.

        Args:
            namespace (str): The target storage namespace or category where the items will be registered.
            items (dict[str, T]): A dictionary mapping unique keys to values being registered in bulk.
        """
        # REGISTRATION DELEGATION: EXTERNAL REGISTER_BULK_ITEMS INVOCATION
        # Delegate bulk item insertion, namespace provisioning, and storage mapping updates
        # to the centralized register_bulk_items utility, passing the storage structure, namespace, and items dictionary.
        register_bulk_items(self._storage, namespace, items)

    # PERSISTENCE & STORAGE SUBSYSTEM: ITEM RETRIEVAL & LAZY EVALUATION
    # This method retrieves a single item from a specified namespace within the internal storage container,
    # delegating to the external get_item utility to automatically evaluate and cache stored callables (factories/lazy loaders),
    # returning the resolved item or a default fallback if not found.
    def get(self, namespace: str, key: str, default: T | None = None) -> T | None:
        """
        Retrieve a single item from a namespace, automatically evaluating any stored
        callables (factories or lazy loaders) on-the-fly with singleton caching.

        Args:
            namespace (str): The target storage namespace or category to query.
            key (str): The unique identifier key of the item within the namespace.
            default (T | None, optional): The default fallback value to return if the key is not found. Defaults to None.

        Returns:
            T | None: The retrieved item value (evaluated if callable), or the default value if the item does not exist.
        """
        # RETRIEVAL DELEGATION: EXTERNAL GET_ITEM INVOCATION WITH LAZY RESOLUTION
        # Delegate secure item lookup and transparent callable evaluation within the storage
        # container namespace to the centralized get_item utility, passing the storage dictionary,
        # namespace, key, and default value.
        return get_item(self._storage, namespace, key, default)

    # PERSISTENCE & STORAGE SUBSYSTEM: MANDATORY ITEM RETRIEVAL
    # This method retrieves a mandatory item from a specified namespace, ensuring strict existence
    # and dynamic type safety by raising a RuntimeError if missing and casting to the expected type V.
    def require(self, namespace: str, key: str, expected_type: type[V]) -> V:
        """
        Retrieve a mandatory item from a namespace and cast it to the expected type V.
        Raises a RuntimeError if the item is not found, guaranteeing a precise non-None return type.

        Args:
            namespace (str): The target storage namespace or category to query.
            key (str): The unique identifier key of the mandatory item.
            expected_type (type[V]): The target class or type to cast and bind the retrieved item to.

        Returns:
            V: The retrieved mandatory item cast to the expected type V.

        Raises:
            RuntimeError: If the requested item does not exist within the specified namespace.
        """
        # ITEM RETRIEVAL DELEGATION
        # Attempt to fetch the item from the storage container using the internal get method.
        item = self.get(namespace, key)

        # MANDATORY EXISTENCE VALIDATION
        # Check if the retrieved item evaluates to None; raise a descriptive RuntimeError if missing.
        if item is None:
            raise RuntimeError(
                f"Required registry item '{key}' in namespace '{namespace}' was not found."
            )

        # SUCCESSFUL TYPE-SAFE RETURN
        # Return the validated, non-None item explicitly cast to the method-level generic type V.
        return cast(V, item)

    # PERSISTENCE & STORAGE SUBSYSTEM: NAMESPACE DICTIONARY RETRIEVAL
    # This method retrieves the entire dictionary mapping for a specified namespace within the internal storage container
    # by delegating to an external retrieval utility, returning the complete key-value collection for that namespace.
    def get_namespace(self, namespace: str) -> dict[str, T]:
        """
        Retrieve the entire dictionary of a namespace.

        Args:
            namespace (str): The target storage namespace or category to retrieve.

        Returns:
            dict[str, T]: A dictionary mapping keys to values for the specified namespace.
        """
        # RETRIEVAL DELEGATION: EXTERNAL GET_NAMESPACE_DICT INVOCATION
        # Delegate secure namespace dictionary lookup within the storage container
        # to the centralized get_namespace_dict utility, passing the storage dictionary and target namespace.
        return get_namespace_dict(self._storage, namespace)

    # PERSISTENCE & STORAGE SUBSYSTEM: REGISTRY INSPECTION & DUMPING
    # This method exports a thread-safe snapshot of the entire internal storage structure
    # across all namespaces, delegating to a centralized dump utility for attribute expansion and diagnostics.
    def dump(self) -> dict[str, dict[str, object]]:
        """
        Exports a safe, isolated copy of the entire registry storage dictionary,
        unpacking attributes for clean inspection and diagnostic auditing.

        Returns:
            dict[str, dict[str, object]]: A structured dictionary mapping namespaces
            to their corresponding stored records with expanded attribute states.
        """
        # STORAGE CASTING & UTILITY DELEGATION
        # Cast the internal storage mapping to standard object types and delegate
        # to the centralized dump_storage utility for robust inspection and attribute unpacking.
        return dump_storage(cast(dict[str, dict[str, object]], self._storage))
