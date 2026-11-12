from typing import Any, Callable


# ACTION REGISTRY SUBSYSTEM: DYNAMIC MENU OPTION REGISTRATION
# This utility dynamically registers new menu options, conditions, and handlers into the actions master registry.
# [>] EXECUTING ACTION REGISTRATION ROUTINE
def register_action(
    actions: dict[str, dict[str, Any]],
    key: str,
    label: str,
    condition: Callable[[dict[str, Any]], bool],
    handler: Callable[..., tuple[bool, dict[str, Any]]],
    default: bool = False,
) -> None:
    """
    Registers a new menu option dynamically into the actions master registry.

    Args:
        actions (dict[str, dict[str, Any]]): The master dictionary containing registered action mappings.
        key (str): Unique identifier key for the menu action.
        label (str): Human-readable text label displayed on the menu interface.
        condition (Callable[[dict[str, Any]], bool]): Predicate function evaluated to determine if the action is available.
        handler (Callable[..., tuple[bool, dict[str, Any]]]): Callable handler routine executed when the action is invoked.
        default (bool, optional): Boolean flag indicating whether the action serves as the default selection. Defaults to False.

    Returns:
        None: Modifies the actions dictionary in place.
    """
    # REGISTRY MUTATION: ACTION RECORD INSERTION
    # Assigns the dictionary containing metadata, evaluation predicates, execution handlers,
    # and default flags to the specified action key in the master registry.
    actions[key] = {
        "key": key,
        "label": label,
        "condition": condition,
        "handler": handler,
        "default": default,
    }
