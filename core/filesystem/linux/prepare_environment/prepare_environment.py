import os
import sys


# PATH RESOLUTION PIPELINE
# This module implements a dynamic execution environment configuration system.
# By prioritizing local development directories over production fallbacks,
# we ensure that developers can safely test live code modifications without
# polluting global package paths.
def prepare_environment(prod_path: str, dev_path: str | None = None) -> None:
    """
    Dynamically configures sys.path to prioritize a local development
    path over a production fallback.

    This engine bridges the gap between local development setups and deployment
    environments by dynamically adjusting module search priorities. The path
    resolution sequence is governed by path presence and expansion checks.

    Args:
        prod_path: The default filesystem path for production assets or libraries.
        dev_path: Optional override path pointing to an active development directory.
    """

    # PATH EXPANSION GATE: USER SYMBOL RESOLUTION
    # We expand tilde (~) shortcuts across both potential target paths.
    # This normalizes relative user paths into absolute filesystem references.
    # [>] EXPANDING USER SYMBOLS
    expanded_dev = os.path.expanduser(dev_path) if dev_path else None
    expanded_prod = os.path.expanduser(prod_path)

    # PATH EVALUATION GATE: DEVELOPMENT OVERRIDE RESOLUTION
    # If a development path is provided, we verify its existence on the filesystem.
    # We select the production path as our fallback target if validation fails.
    # [>] RESOLVING TARGET PATH
    if expanded_dev and os.path.exists(expanded_dev):
        target_path = expanded_dev
    else:
        target_path = expanded_prod

    # DUP-CHECK GATE: IDEMPOTENT PATH INJECTION
    # We check the leading index of sys.path before performing an insertion.
    # This prevents redundant entries from accumulating during repetitive invocations.
    # [>] EVALUATING PATH STATE
    if sys.path[0] != target_path:
        # PREPEND EXECUTION PATH: LOCAL PRIORITY INJECTION
        # We inject the target path at index 0 of sys.path.
        # This guarantees that the interpreter resolves local overrides first.
        sys.path.insert(0, target_path)

