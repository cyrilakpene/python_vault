from typing import Any, Callable

from .registry import register_action  # type: ignore[import-not-found]
from .evaluator import filter_active_actions  # type: ignore[import-not-found]
from .prompt import build_and_prompt  # type: ignore[import-not-found]


# DYNAMIC MENU ORCHESTRATION & INTERACTIVE STATE MACHINE
# CONCRETE CONTROLLER: RUNTIME NAVIGATION & DISPATCH ENGINE
# Orchestrates dynamic menu generation, user prompt loops, and interactive state transitions.
# By resolving nested command registries and runtime user inputs, it guarantees a responsive,
# modular, and fault-tolerant command-line user interface.
class DynamicMenuEngine:
    """
    Orchestrates dynamic menu generation, user prompt loops, and interactive state transitions.

    Provides modular command routing, state tracking, and flexible user input parsing,
    ensuring a cohesive and extensible interactive experience across runtime workflows.
    """

    # PIPELINE ACTION SUBSYSTEM: ACTIONS INITIALIZER
    # This initializer sets up the action registry container, provisioning a nested dictionary
    # mapping structure to organize executable actions, metadata, and handlers by namespace and identifier.
    def __init__(self) -> None:
        """
        Initializes the action registry container with an empty nested dictionary mapping.
        """
        # ACTION STORAGE STRUCTURE INITIALIZATION
        # Initialize the private actions dictionary to store action metadata, handlers, and configurations.
        self.actions: dict[str, dict[str, Any]] = {}

    # PIPELINE ACTION SUBSYSTEM: DYNAMIC MENU OPTION REGISTRATION
    # This method registers a new menu option dynamically into the internal actions registry
    # by delegating to an external registration utility, binding keys, display labels, evaluation conditions, handlers, and defaults.
    def register(
        self,
        key: str,
        label: str,
        condition: Callable[[dict[str, Any]], bool],
        handler: Callable[..., tuple[bool, dict[str, Any]]],
        default: bool = False,
    ) -> None:
        """
        Registers a new menu option dynamically, specifying its unique key, display label,
        evaluation condition, execution handler, and default state.

        Args:
            key (str): The unique identifier key for the menu option.
            label (str): The human-readable display label for the menu option.
            condition (Callable[[dict[str, Any]], bool]): A callable function that evaluates context data
                to determine whether the menu option is active or available.
            handler (Callable[..., tuple[bool, dict[str, Any]]]): A callable function executed when the option
                is selected, returning a status flag and updated context dictionary.
            default (bool, optional): Flag indicating whether this option serves as the default. Defaults to False.
        """
        # ACTION REGISTRATION DELEGATION
        # Delegate registration, validation, and storage of the action metadata, condition, and handlers
        # to the centralized register_action utility, passing the internal actions registry and parameters.
        register_action(self.actions, key, label, condition, handler, default)

    # PIPELINE ACTION SUBSYSTEM: DYNAMIC PROMPT & EXECUTION
    # This method filters registered actions based on runtime conditions, builds dynamic CLI prompts,
    # collects user input, and executes the corresponding action handler or returns default failure states.
    def prompt_and_execute(
        self, context: dict[str, Any], registry: dict[str, Any]
    ) -> tuple[bool, dict[str, Any]]:
        """
        Filters active actions based on runtime conditions, prompts the user interactively,
        and executes the selected handler with context and registry references.

        Args:
            context (dict[str, Any]): The current runtime context dictionary containing pipeline state.
            registry (dict[str, Any]): The registry container dictionary accessible by action handlers.

        Returns:
            tuple[bool, dict[str, Any]]: A tuple containing a continuation/success boolean flag
            and the updated context dictionary returned by the executed handler.
        """
        # ACTIVE ACTION FILTERING
        # Filter the registered actions dictionary against the current runtime context
        # using the external filter_active_actions utility to determine available options.
        active_actions = filter_active_actions(self.actions, context)

        # PROMPT GENERATION & INPUT COLLECTION
        # Build dynamic CLI prompt options from the active actions and collect user selection choice
        # via the external build_and_prompt utility.
        choice, _ = build_and_prompt(active_actions)

        # HANDLER DISPATCH & EXECUTION
        # Validate that the user's choice exists in the active actions dictionary,
        # extract its registered handler, and execute it passing the context and registry.
        if choice in active_actions:
            handler_func = active_actions[choice]["handler"]
            return handler_func(context, registry)

        # FALLBACK DEFAULT RETURN
        # Return a default failure tuple if the choice is invalid or no action was executed.
        return False, registry
