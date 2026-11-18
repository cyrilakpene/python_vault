from typing import Any, Callable

from .registry import register_step  # type: ignore[import-not-found]
from .prompt import build_and_prompt  # type: ignore[import-not-found]


# WORKFLOW SUBSYSTEM: INITIAL STATE RESOLUTION & CONFIGURATION EXTRACTION
# This utility resolves workflow definitions, states dictionaries, and initial state keys
# from configuration mappings to bootstrap state machine execution loops.
# [>] EXECUTING INITIAL STATE RESOLUTION
def _resolve_initial_state(
    run_key: str, workflow_config: dict[str, Any]
) -> tuple[dict[str, Any] | None, dict[str, Any], str | None]:
    """
    Resolves the workflow definition, states dictionary, and initial state key.

    Args:
        run_key (str): The unique string key identifying the workflow run configuration.
        workflow_config (dict[str, Any]): Dictionary containing available workflow definitions and configurations.

    Returns:
        tuple[dict[str, Any] | None, dict[str, Any], str | None]: A tuple containing the workflow definition dictionary,
        the states dictionary, and the initial state key string.
    """
    # WORKFLOW DEFINITION RETRIEVAL
    # Retrieves the workflow run definition corresponding to the specified run key.
    run_def = workflow_config.get(run_key)
    if not run_def:
        return None, {}, None

    # STATES & INITIAL STATE EXTRACTION
    # Extracts the prompts dictionary and initial state identifier from the workflow definition.
    states = run_def.get("prompts", {})
    initial_state = run_def.get("initial_state")

    # RESOLVED WORKFLOW TUPLE RETURN
    # Returns the workflow definition, states dictionary, and initial state key.
    return run_def, states, initial_state


# WORKFLOW SUBSYSTEM: STATE GRAPH EXECUTION & TRANSITION RESOLUTION
# This utility iterates through workflow state graphs, executing individual step logic,
# processing transition signals, and resolving subsequent target states until completion.
# [>] EXECUTING WORKFLOW STATE GRAPH ITERATION
def _execute_workflow_loop(
    states: dict[str, Any],
    current_state_key: str | None,
    steps: dict[str, dict[str, Any]],
    context: dict[str, Any],
    registry: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    """
    Iterates through the state graph, executing steps and resolving transitions.

    Args:
        states (dict[str, Any]): Dictionary containing state configurations and prompt definitions.
        current_state_key (str | None): String identifier for the current active state in the graph.
        steps (dict[str, dict[str, Any]]): Dictionary mapping state keys to their execution step definitions.
        context (dict[str, Any]): Runtime context dictionary tracking execution data and variables.
        registry (dict[str, Any]): Global registry dictionary maintaining configuration and session state.

    Returns:
        tuple[bool, dict[str, Any]]: A tuple containing a boolean success status and the updated runtime context.
    """
    # STATE GRAPH ITERATION LOOP
    # Continues execution while an active state key exists in the workflow graph traversal.
    while current_state_key:
        state_cfg = states.get(current_state_key)
        step_def = steps.get(current_state_key)

        # STATE & STEP VALIDATION GUARD
        # Terminates execution and returns failure status if state configurations or step definitions are missing.
        if not state_cfg or not step_def:
            return False, registry

        # STATE STEP EXECUTION & SIGNAL RESOLUTION
        # Executes the individual workflow step, handling automatic natural flows or interactive operator prompts.
        transition_signal, context = _execute_state_step(
            state_cfg, step_def, steps, context, registry
        )

        # NEXT TRANSITION RESOLUTION
        # Resolves the next target state key from the state configuration based on the returned transition signal.
        current_state_key = _resolve_next_transition(state_cfg, transition_signal)

    # WORKFLOW COMPLETION RETURN
    # Returns success status and the finalized runtime context upon successful graph termination.
    return True, context


# WORKFLOW SUBSYSTEM: STATE STEP EXECUTION & MODE DISPATCH
# This utility executes individual workflow steps according to their execution mode (automatic natural flow
# or interactive operator prompting), dispatching handlers and resolving option selections.
# [>] EXECUTING WORKFLOW STATE STEP DISPATCH
def _execute_state_step(
    state_cfg: dict[str, Any],
    step_def: dict[str, Any],
    steps: dict[str, dict[str, Any]],
    context: dict[str, Any],
    registry: dict[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    """
    Executes a single step based on its mode (automatic natural flow or interactive).

    Args:
        state_cfg (dict[str, Any]): Configuration dictionary defining the current state parameters and options.
        step_def (dict[str, Any]): Step definition dictionary containing handlers, modes, and labels.
        steps (dict[str, dict[str, Any]]): Dictionary mapping state keys to their respective step definitions.
        context (dict[str, Any]): Runtime context dictionary tracking execution data and variables.
        registry (dict[str, Any]): Global registry dictionary maintaining configuration and session state.

    Returns:
        tuple[str | None, dict[str, Any]]: A tuple containing the transition signal string or None, and the updated runtime context.
    """
    # HANDLER & MODE RESOLUTION
    # Extracts the execution handler function and resolves the operational mode from state config or step definitions.
    handler = step_def["handler"]
    mode = state_cfg.get("mode", step_def["mode"])

    # AUTOMATIC MODE EXECUTION
    # Executes the handler directly for natural flow automation without interactive prompts or options.
    if mode == "automatic":
        return handler(context, registry)

    # AVAILABLE OPTIONS & INTERACTIVE PROMPT GENERATION
    # Checks for configured options, compiling active prompt option mappings with labels and default flags.
    available_options = state_cfg.get("options", {})
    if available_options:
        active_prompt_options = {
            k: {
                "label": steps[k]["label"],
                "default": (k == state_cfg.get("default")),
            }
            for k in available_options
            if k in steps
        }

        # PROMPT BUILDER INVOCATION & CHOICE CAPTURE
        # Prompts the operator with active options and captures the selected transition choice.
        choice, _ = build_and_prompt(active_prompt_options)
        return choice, context

    # FALLBACK HANDLER EXECUTION
    # Invokes the step handler directly if no interactive options are defined.
    return handler(context, registry)


# WORKFLOW SUBSYSTEM: TRANSITION RESOLUTION & STATE GRAPH ROUTING
# This utility evaluates state configuration transition mappings against returned transition signals
# to determine and route to the subsequent target state key within the workflow graph.
# [>] EXECUTING TRANSITION RESOLUTION
def _resolve_next_transition(
    state_cfg: dict[str, Any], transition_signal: str | None
) -> str | None:
    """
    Evaluates transition mappings to determine the next state in the graph.

    Args:
        state_cfg (dict[str, Any]): Configuration dictionary defining state transition mappings and routing rules.
        transition_signal (str | None): The signal string or choice returned from the executed state step.

    Returns:
        str | None: The next target state key string, or the transition signal itself if no mapping matches.
    """
    # TRANSITIONS DICTIONARY EXTRACTION
    # Extracts transition mapping dictionaries from the state configuration.
    transitions = state_cfg.get("transitions", {})

    # SIGNAL MATCH EVALUATION & DEFAULT FALLBACK
    # Evaluates if the transition signal matches an explicit mapping, or falls back to default routes if available.
    if transition_signal in transitions:
        return transitions[transition_signal]
    elif "default" in transitions:
        return transitions["default"]

    # RAW TRANSITION SIGNAL RETURN
    # Returns the raw transition signal if no explicit or default transition mapping is found.
    return transition_signal


# CONFIG-DRIVEN WORKFLOW ORCHESTRATION & NON-LINEAR GRAPH ENGINE
# CONCRETE CONTROLLER: MODULAR HELPER DELEGATION & STATE ROUTING
# Orchestrates config-driven, non-linear workflow graphs by delegating execution logic
# to modular helper functions. By decoupling workflow definitions from control-flow implementation,
# it enables flexible, dynamic execution paths and maintainable interactive pipelines.
class DynamicMenuEngine:
    """
    Orchestrates config-driven, non-linear workflow graphs
    by delegating execution logic to modular helper functions.

    Provides dynamic path resolution, workflow graph traversal, and decoupled helper
    delegation, ensuring flexible and maintainable multi-step execution flows.
    """

    # WORKFLOW SUBSYSTEM: STEP REGISTRY INITIALIZER
    # This initializer sets up the workflow step registry container, provisioning a nested dictionary
    # mapping structure to organize pipeline steps, metadata, and execution callbacks by identifier.
    def __init__(self) -> None:
        """
        Initializes the workflow step registry container with an empty nested dictionary mapping.
        """
        # STEP STORAGE STRUCTURE INITIALIZATION
        # Initialize the private steps dictionary to store step metadata, configurations, and callbacks.
        self.steps: dict[str, dict[str, Any]] = {}

    # WORKFLOW SUBSYSTEM: NON-LINEAR STEP REGISTRATION
    # This method registers a non-linear workflow execution step into the internal step registry
    # by delegating to an external registration utility, binding the step key, label, handler, and execution mode.
    def register_step(
        self,
        key: str,
        handler: Callable[..., tuple[str | None, dict[str, Any]]],
        label: str | None = None,
        mode: str = "interactive",
    ) -> None:
        """
        Registers a non-linear workflow execution step, specifying its unique key, display label,
        execution handler callback, and operating mode.

        Args:
            key (str): The unique identifier key for the workflow step.
            label (str | None): The human-readable display label for the workflow step.
            handler (Callable[..., tuple[str | None, dict[str, Any]]]): The callable execution handler
                for the step, returning a next-step target indicator and updated context dictionary.
            mode (str, optional): The execution mode for the step (e.g., "interactive", "batch").
                Defaults to "interactive".
        """
        # STEP REGISTRATION DELEGATION
        # Delegate registration, metadata validation, and storage of the workflow step
        # to the centralized register_step utility, passing the internal steps registry and parameters.
        register_step(self.steps, key, label, handler, mode)

    # WORKFLOW SUBSYSTEM: GRAPH WORKFLOW EXECUTION ENTRY POINT
    # This method serves as the main entry point for graph-based workflow execution,
    # resolving initial state configurations and delegating workflow loop orchestration to modular helpers.
    def execute_workflow(
        self,
        run_key: str,
        workflow_config: dict[str, Any],
        context: dict[str, Any],
        registry: dict[str, Any],
    ) -> tuple[bool, dict[str, Any]]:
        """
        Main entry point for graph workflow execution. Resolves initial states from configuration
        and delegates orchestration loop execution to modular helper functions.

        Args:
            run_key (str): The unique run key identifying the workflow execution configuration.
            workflow_config (dict[str, Any]): The workflow configuration dictionary containing states and rules.
            context (dict[str, Any]): The current runtime context dictionary carrying execution state.
            registry (dict[str, Any]): The registry container dictionary accessible across workflow steps.

        Returns:
            tuple[bool, dict[str, Any]]: A tuple containing a success/continuation boolean flag
            and the final updated context dictionary.
        """
        # INITIAL STATE RESOLUTION
        # Resolve the initial run definition, state collection, and starting state key
        # from the workflow configuration and run key using the external _resolve_initial_state utility.
        run_def, states, current_state_key = _resolve_initial_state(
            run_key, workflow_config
        )

        # INITIAL STATE VALIDATION
        # Validate that both the run definition and starting state key were successfully resolved;
        # return a failure flag and registry reference immediately if validation fails.
        if not run_def or not current_state_key:
            return False, registry

        # WORKFLOW LOOP EXECUTION DELEGATION
        # Delegate the core graph execution loop to the centralized _execute_workflow_loop utility,
        # passing state definitions, current state key, registered steps, context, and registry.
        return _execute_workflow_loop(
            states, current_state_key, self.steps, context, registry
        )
