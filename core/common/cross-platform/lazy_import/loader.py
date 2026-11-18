import importlib
from typing import Any


# SYSTEM UTILITIES SUBSYSTEM: DYNAMIC MODULE IMPORTATION & CLASS INSTANTIATION
# This utility dynamically imports modules from specified paths, retrieves target class definitions,
# and instantiates them with default parameters.
# [>] EXECUTING CLASS LOADING & INSTANTIATION
def load_and_instantiate_class(module_path: str, class_name: str) -> Any:
    """
    Dynamically imports a module, retrieves a specified class by name, and returns a new instance.

    Args:
        module_path (str): The dot-separated import path of the module (e.g., 'package.module').
        class_name (str): The name of the target class to retrieve and instantiate.

    Returns:
        Any: An instance of the requested class.
    """
    # DYNAMIC MODULE IMPORTATION
    # Imports the Python module dynamically using the provided module path string.
    importlib_module = importlib.import_module(module_path)

    # CLASS ATTRIBUTE RETRIEVAL
    # Retrieves the target class reference from the imported module using its class name.
    cls = getattr(importlib_module, class_name)

    # CLASS INSTANTIATION & RETURN
    # Instantiates the retrieved class and returns the resulting object.
    return cls()
