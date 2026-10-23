from typing import Any, Callable

from .controller import menu_controller  # type: ignore[import-not-found]


# MENU ROUTER & LIFECYCLE MANAGEMENT ENGINE
# This utility manages persistent state routing and execution lifecycle loops for nested sub-menus,
# automatically handling back navigation injection, callable options resolution, and exit conditions.
# [>] EXECUTING MENU ROUTING LIFECYCLE
def menu_router(
    options: (
        dict[str, Callable[..., Any]] | Callable[[], dict[str, Callable[..., Any]]]
    ),
    is_main_menu: bool = False,
    returns_value: bool = False,
    **kwargs: Any,
) -> Any:
    """
    Manages persistent state routing and lifecycle loops for nested sub-menus.

    Args:
        options: Dictionary mapping option labels to callbacks, or a callable returning option dictionaries.
        is_main_menu: Boolean flag indicating if this is the top-level main menu (disables default back injection).
        returns_value: Boolean flag determining whether non-None execution results are immediately returned.
        **kwargs: Additional keyword arguments forwarded to the menu controller.

    Returns:
        Any: The execution result if `returns_value` is enabled, or None upon session termination.
    """
    # BACK NAVIGATION DEFAULT CONFIGURATION
    # Automatically injects backward navigation support into sub-menus unless explicitly configured as the main menu.
    if not is_main_menu:
        kwargs.setdefault("allow_back", True)

    # PERSISTENT LIFECYCLE ROUTING LOOP
    # Continuously evaluates options (resolving dynamic callables if needed) and runs the menu controller,
    # handling navigation back signals, exit requests, and value returns.
    while True:
        resolved_options = options() if callable(options) else options

        result = menu_controller(resolved_options, **kwargs)

        # NAVIGATION BACK CHECK
        # Breaks out of the lifecycle loop if the user triggers a backward navigation signal.
        if result == "BACK":
            break

        # MAIN MENU EXIT CHECK
        # Terminates the lifecycle loop if the main menu registers an explicit exit command.
        if is_main_menu and result == "EXIT":
            break

        # VALUE RETURN GATE
        # Returns the execution result immediately if value-returning mode is enabled and output is valid.
        if returns_value and result is not None:
            return result
