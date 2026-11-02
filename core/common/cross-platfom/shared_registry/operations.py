from typing import Any, TypeVar

# TYPING SUBSYSTEM: GENERIC TYPE VARIABLE DEFINITION
# This utility defines a generic type variable T for use in generic class, function,
# and method type annotations across the type-safe architectural subsystems.
# [>] EXECUTING TYPE VARIABLE DEFINITION
T = TypeVar("T")


# SYSTEM UTILITIES SUBSYSTEM: ITEM REGISTRATION & NAMESPACE STORAGE
# This utility registers individual items within hierarchical storage dictionaries under designated namespaces,
# automatically initializing namespace containers when missing.
# [>] EXECUTING ITEM REGISTRATION
def register_item(
    storage: dict[str, dict[str, Any]], namespace: str, key: str, value: Any
) -> None:
    """
    Registers a single item in storage under a designated namespace, initializing the namespace if missing.

    Args:
        storage (dict[str, dict[str, Any]]): The hierarchical storage dictionary containing namespaces.
        namespace (str): The target namespace key within storage.
        key (str): The specific item key within the namespace.
        value (Any): The value to register.

    Returns:
        None
    """
    # NAMESPACE STABILIZATION & INITIALIZATION
    # Checks if the target namespace exists in storage; if missing, initializes it as an empty dictionary.
    if namespace not in storage:
        storage[namespace] = {}

    # ITEM ASSIGNMENT & REGISTRATION
    # Assigns the given value to the specified key within the target namespace dictionary.
    storage[namespace][key] = value


# SYSTEM UTILITIES SUBSYSTEM: BULK ITEM REGISTRATION & NAMESPACE UPDATE
# This utility registers multiple items in bulk within hierarchical storage dictionaries under designated namespaces,
# automatically initializing namespace containers when missing.
# [>] EXECUTING BULK ITEM REGISTRATION
def register_bulk_items(
    storage: dict[str, dict[str, Any]], namespace: str, items: dict[str, Any]
) -> None:
    """
    Registers multiple items in bulk within a designated namespace, initializing the namespace if missing.

    Args:
        storage (dict[str, dict[str, Any]]): The hierarchical storage dictionary containing namespaces.
        namespace (str): The target namespace key within storage.
        items (dict[str, Any]): A dictionary of key-value pairs to register in bulk.

    Returns:
        None
    """
    # NAMESPACE STABILIZATION & INITIALIZATION
    # Checks if the target namespace exists in storage; if missing, initializes it as an empty dictionary.
    if namespace not in storage:
        storage[namespace] = {}

    # BULK ITEM UPDATE & REGISTRATION
    # Updates the target namespace dictionary with the provided bulk items.
    storage[namespace].update(items)


# SYSTEM UTILITIES SUBSYSTEM: ITEM RETRIEVAL & NAMESPACE LOOKUP
# This utility retrieves a single item from hierarchical storage dictionaries under a designated namespace,
# automatically evaluating stored callables (factories/lazy loaders) on-the-fly with singleton caching,
# or falling back to a default value if the namespace or key is missing.
# [>] EXECUTING ITEM RETRIEVAL & LAZY EVALUATION
def get_item(
    storage: dict[str, dict[str, Any]], namespace: str, key: str, default: Any = None
) -> Any:
    """
    Retrieves a single item from storage under a designated namespace, evaluating
    any stored callables (factories or lazy loaders) on-the-fly and caching the result,
    or returning a default if unfound.

    Args:
        storage (dict[str, dict[str, Any]]): The hierarchical storage dictionary containing namespaces.
        namespace (str): The target namespace key within storage.
        key (str): The specific item key within the namespace.
        default (Any): The default value to return if the namespace or key does not exist. Defaults to None.

    Returns:
        Any: The retrieved item value (evaluated if callable), or the default value if not found.
    """
    # NAMESPACE & ITEM LOOKUP
    # Safely accesses the namespace dictionary within storage and retrieves the raw item value.
    item = storage.get(namespace, {}).get(key, default)

    # CALLABLE EVALUATION & LAZY RESOLUTION (SINGLETON CACHING)
    # Checks if the retrieved item is callable (e.g., a lambda or factory function).
    # If so, it executes the callable to resolve the resource, caches the resulting
    # instance back into storage to enforce a singleton lifecycle, and returns it.
    if callable(item):
        resolved_value = item()
        if namespace in storage and key in storage[namespace]:
            storage[namespace][key] = resolved_value
        return resolved_value

    return item


# SYSTEM UTILITIES SUBSYSTEM: NAMESPACE DICTIONARY RETRIEVAL & STORAGE LOOKUP
# This utility retrieves an entire namespace dictionary from hierarchical storage,
# falling back to an empty dictionary if the namespace does not exist.
# [>] EXECUTING NAMESPACE DICTIONARY RETRIEVAL
def get_namespace_dict(
    storage: dict[str, dict[str, Any]], namespace: str
) -> dict[str, Any]:
    """
    Retrieves an entire namespace dictionary from storage, returning an empty dictionary if unfound.

    Args:
        storage (dict[str, dict[str, Any]]): The hierarchical storage dictionary containing namespaces.
        namespace (str): The target namespace key to retrieve.

    Returns:
        dict[str, Any]: The retrieved namespace dictionary, or an empty dictionary if not found.
    """
    # NAMESPACE DICTIONARY LOOKUP
    # Safely accesses and returns the namespace dictionary from storage, defaulting to an empty dictionary.
    return storage.get(namespace, {})


# SYSTEM UTILITIES SUBSYSTEM: STORAGE DUMPING & SERIALIZATION EXPORT
# This utility exports and serializes hierarchical storage items by extracting public attributes
# from both class definitions and instance dictionaries across all namespaces.
# [>] EXECUTING STORAGE DUMP
def dump_storage(storage: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    """
    Exports and serializes hierarchical storage items by extracting public attributes from classes and instances.

    Args:
        storage (dict[str, dict[str, object]]): The hierarchical storage dictionary containing namespaces and items.

    Returns:
        dict[str, dict[str, object]]: An exported dictionary mapping namespaces to serialized public attributes.
    """
    # EXPORT CONTAINER INITIALIZATION
    # Initializes the root dictionary to hold the exported namespace mappings.
    exported: dict[str, dict[str, object]] = {}

    # NAMESPACE ITERATION & TRAVERSAL
    # Iterates through each namespace and its corresponding items within storage.
    for namespace, items in storage.items():
        ns_dict: dict[str, object] = {}
        for key, value in items.items():
            combined_attrs: dict[str, object] = {}

            # TARGET CLASS RESOLUTION
            # Determines if the stored value is a class or an instance to extract appropriate attributes.
            target_cls = value if isinstance(value, type) else type(value)

            # CLASS-LEVEL ATTRIBUTE EXTRACTION
            # Extracts non-private public attributes from the target class dictionary.
            for attr, val in target_cls.__dict__.items():
                if not attr.startswith("_"):
                    combined_attrs[attr] = val

            # INSTANCE-LEVEL ATTRIBUTE EXTRACTION
            # Extracts non-private public attributes from the instance dictionary if value is an instance.
            if not isinstance(value, type) and hasattr(value, "__dict__"):
                for attr, val in value.__dict__.items():
                    if not attr.startswith("_"):
                        combined_attrs[attr] = val

            ns_dict[key] = combined_attrs
        exported[namespace] = ns_dict

    # EXPORTED STORAGE RETURN
    # Returns the fully serialized and dumped storage dictionary.
    return exported
