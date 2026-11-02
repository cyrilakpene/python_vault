from typing import Any

from .loader import load_and_instantiate_class  # type: ignore[import-not-found]


# LAZY INITIALIZATION & DEFERRED MODULE IMPORT ORCHESTRATOR
# CONCRETE LOADER: ON-DEMAND RESOURCE RESOLUTION & PROXY ENGINE
# Defers module imports, heavy assets, or resource initialization until first explicit access.
# By eliminating premature startup overhead, it optimizes memory usage and accelerates application boot times.
class LazyLoader:
    """
    Defers resource allocation and module importation until first explicit access.

    This class provides proxy-based lazy loading to eliminate premature startup overhead,
    optimizing initialization performance and conserving system memory across deferred dependencies.
    """

    # PIPELINE CONTAINER SUBSYSTEM: LAZY LOADER INITIALIZATION
    # This initializer sets up a dynamic module and class reference for lazy loading,
    # storing the module import path, target class name, and an internal cache for the instantiated object.
    def __init__(self, module_path: str, class_name: str):
        """
        Initializes the dynamic module loader with target module path and class name parameters.

        Args:
            module_path (str): The dotted import path of the target Python module.
            class_name (str): The name of the target class to be dynamically loaded and instantiated.
        """
        # MODULE PATH & CLASS NAME ASSIGNMENT
        # Store the target module import path and the class name for subsequent dynamic resolution.
        self.module_path = module_path
        self.class_name = class_name

        # INSTANCE CACHE INITIALIZATION
        # Initialize the internal instance cache as None to support lazy loading and singleton caching.
        self._loaded_instance: Any | None = None

    # PIPELINE CONTAINER SUBSYSTEM: LAZY LOADER INVOCATION
    # This method enables the loader instance to act as a callable, checking the internal cache
    # and dynamically importing and instantiating the target class on first access.
    def __call__(self) -> Any:
        """
        Invokes the loader, returning the cached instance or dynamically importing and
        instantiating the target class if it has not yet been loaded.

        Returns:
            Any: The loaded and instantiated class instance.
        """
        # CACHE CHECK & LAZY INSTANTIATION
        # Check if the target instance has already been loaded; if not, delegate to the
        # external dynamic loading and instantiation utility using the stored module path and class name.
        if self._loaded_instance is None:
            self._loaded_instance = load_and_instantiate_class(
                self.module_path, self.class_name
            )

        # CACHED INSTANCE RETURN
        # Return the cached instance, ensuring efficient singleton-like access across subsequent calls.
        return self._loaded_instance
