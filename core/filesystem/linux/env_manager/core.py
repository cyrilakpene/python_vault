from .expander import expand_paths
from .path_injector import inject_path
from .validator import resolve_target_path


# ENVIRONMENT PREPARATION & RUNTIME BOOTSTRAP ENGINE
# This utility orchestrates environment configuration by expanding file paths,
# resolving development overrides against production fallbacks, and idempotently
# injecting the selected target into Python's module search path.
# [>] EXECUTING ENVIRONMENT PREPARATION & BOOTSTRAP
def prepare_environment(prod_path: str, dev_path: str | None = None) -> None:
    """
    Dynamically configures sys.path to prioritize a local development
    path over a production fallback.

    Args:
        prod_path: The primary production directory path string.
        dev_path: Optional secondary development directory path string for local overrides.
    """
    # PATH EXPANSION & RESOLUTION INVOCATION
    # Expands tilde shortcuts across both production and development paths
    # and selects the appropriate target based on filesystem existence.
    expanded_prod, expanded_dev = expand_paths(prod_path, dev_path)
    target_path = resolve_target_path(expanded_prod, expanded_dev)

    # SYS.PATH INJECTION & BOOTSTRAP FINALIZATION
    # Injects the resolved target path into Python's module search path
    # to guarantee correct import prioritization.
    inject_path(target_path)
