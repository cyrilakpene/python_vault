from typing import Any, Callable

from .registry import register_step  # type: ignore[import-not-found]
from .prompt import build_and_prompt  # type: ignore[import-not-found]
from .constants import report_status, LogContext, log_path, context  # type: ignore[import-not-found]


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
        report_status(
            state="warn",
            message=f"Workflow run key {run_key!r} not found in configuration.",
            context=LogContext(
                component="prompt_engine",
                log_path=log_path,
                trace_id="interface.prompt_engine",
                actor=context.get("user"),
                payload={
                    "run_key": run_key,
                    "available_keys": list(workflow_config.keys()),
                },
            ),
        )
        return None, {}, None

    # STATES & INITIAL STATE EXTRACTION
    # Extracts the prompts dictionary and initial state identifier from the workflow definition.
    states = run_def.get("prompts", {})
    initial_state = run_def.get("initial_state")

    if not initial_state:
        report_status(
            state="warn",
            message=f"Workflow run {run_key!r} is missing an 'initial_state'.",
            context=LogContext(
                component="prompt_engine",
                log_path=log_path,
                trace_id="interface.prompt_engine",
                actor=context.get("user"),
                payload={
                    "run_key": run_key,
                    "has_prompts": bool(states),
                },
            ),
        )

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
    state_context: dict[str, Any],
    registry: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    """
    Iterates through the state graph, executing steps and resolving transitions.

    Args:
        states (dict[str, Any]): Dictionary containing state configurations and prompt definitions.
        current_state_key (str | None): String identifier for the current active state in the graph.
        steps (dict[str, dict[str, Any]]): Dictionary mapping state keys to their execution step definitions.
        state_context (dict[str, Any]): Runtime context dictionary tracking execution data and variables.
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
            report_status(
                state="fail",
                message=(
                    f"Missing state configuration or step definition for state "
                    f"{current_state_key!r}; aborting workflow."
                ),
                context=LogContext(
                    component="pompt_engine",
                    log_path=log_path,
                    trace_id="interface.pompt_engine",
                    actor=context.get("user"),
                    payload={
                        "state_key": current_state_key,
                        "has_state_cfg": bool(state_cfg),
                        "has_step_def": bool(step_def),
                    },
                ),
            )
            return False, registry

        # STATE STEP EXECUTION & SIGNAL RESOLUTION
        # Executes the individual workflow step, handling automatic natural flows or interactive operator prompts.
        transition_signal, state_context = _execute_state_step(
            state_cfg, step_def, steps, state_context, registry
        )

        # NEXT TRANSITION RESOLUTION
        # Resolves the next target state key from the state configuration based on the returned transition signal.
        current_state_key = _resolve_next_transition(state_cfg, transition_signal)

    # WORKFLOW COMPLETION RETURN
    # Returns success status and the finalized runtime context upon successful graph termination.
    return True, state_context


# WORKFLOW SUBSYSTEM: STATE STEP EXECUTION & MODE DISPATCH
# This utility executes individual workflow steps according to their execution mode (automatic natural flow
# or interactive operator prompting), dispatching handlers and resolving option selections.
# [>] EXECUTING WORKFLOW STATE STEP DISPATCH
def _execute_state_step(
    state_cfg: dict[str, Any],
    step_def: dict[str, Any],
    steps: dict[str, dict[str, Any]],
    state_context: dict[str, Any],
    registry: dict[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    """
    Executes a single step based on its mode (automatic natural flow or interactive).

    Args:
        state_cfg (dict[str, Any]): Configuration dictionary defining the current state parameters and options.
        step_def (dict[str, Any]): Step definition dictionary containing handlers, modes, and labels.
        steps (dict[str, dict[str, Any]]): Dictionary mapping state keys to their respective step definitions.
        state_context (dict[str, Any]): Runtime context dictionary tracking execution data and variables.
        registry (dict[str, Any]): Global registry dictionary maintaining configuration and session state.

    Returns:
        tuple[str | None, dict[str, Any]]: A tuple containing the transition signal string or None, and the updated runtime context.
    """
    # HANDLER & MODE RESOLUTION
    # Extracts the execution handler function and resolves the operational mode from state config or step definitions.
    handler = step_def["handler"]
    mode = state_cfg.get("mode", step_def.get("mode", "interactive"))
    step_key = step_def.get("key", "<unknown>")

    if mode not in {"automatic", "interactive"}:
        report_status(
            state="warn",
            message=(
                f"Unknown execution mode {mode!r} for step {step_key!r}; "
                "defaulting to 'interactive'."
            ),
            context=LogContext(
                component="pompt_engine",
                log_path=log_path,
                trace_id="interface.pompt_engine",
                actor=context.get("user"),
                payload={
                    "step_key": step_key,
                    "mode": mode,
                },
            ),
        )
        mode = "interactive"

    # AUTOMATIC MODE EXECUTION
    # Executes the handler directly for natural flow automation without interactive prompts or options.
    if mode == "automatic":
        try:
            return handler(state_context, registry)
        except Exception as exc:
            report_status(
                state="fail",
                message=f"Automatic handler failed for step {step_key!r}: {exc}.",
                context=LogContext(
                    component="pompt_engine",
                    log_path=log_path,
                    trace_id="interface.pompt_engine",
                    actor=context.get("user"),
                    exception=str(exc),
                    payload={
                        "step_key": step_key,
                        "mode": mode,
                    },
                ),
            )
            raise

    # AVAILABLE OPTIONS & INTERACTIVE PROMPT GENERATION
    # Checks for configured options, compiling active prompt option mappings with labels and default flags.
    available_options = state_cfg.get("options", {})
    if available_options:
        active_prompt_options: dict[str, dict[str, Any]] = {}
        for k in available_options:
            if k not in steps:
                report_status(
                    state="warn",
                    message=(
                        f"Option key {k!r} in step {step_key!r} is missing from "
                        "registered steps; skipping option."
                    ),
                    context=LogContext(
                        component="pompt_engine",
                        log_path=log_path,
                        trace_id="interface.pompt_engine",
                        actor=context.get("user"),
                        payload={
                            "step_key": step_key,
                            "option_key": k,
                        },
                    ),
                )
                continue

            option_entry: dict[str, Any] = {
                "label": steps[k]["label"],
                "default": (k == state_cfg.get("default")),
            }
            if "condition" in steps[k]:
                option_entry["condition"] = steps[k]["condition"]
            active_prompt_options[k] = option_entry

        # PROMPT BUILDER INVOCATION & CHOICE CAPTURE
        # Prompts the operator with active options and captures the selected transition choice.
        choice, _ = build_and_prompt(active_prompt_options, state_context=state_context)
        return choice, state_context

    # FALLBACK HANDLER EXECUTION
    # Invokes the step handler directly if no interactive options are defined.
    try:
        return handler(state_context, registry)
    except Exception as exc:
        report_status(
            state="fail",
            message=f"Handler failed for step {step_key!r}: {exc}.",
            context=LogContext(
                component="pompt_engine",
                log_path=log_path,
                trace_id="interface.pompt_engine",
                actor=context.get("user"),
                exception=str(exc),
                payload={
                    "step_key": step_key,
                    "mode": mode,
                },
            ),
        )
        raise


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
        report_status(
            state="warn",
            message=(
                f"Transition signal {transition_signal!r} not in transitions; "
                f"falling back to 'default' ({transitions['default']!r})."
            ),
            context=LogContext(
                component="pompt_engine",
                log_path=log_path,
                trace_id="interface.pompt_engine",
                actor=context.get("user"),
                payload={
                    "transition_signal": transition_signal,
                    "default_target": transitions["default"],
                    "available_transitions": list(transitions.keys()),
                },
            ),
        )
        return transitions["default"]

    # RAW TRANSITION SIGNAL RETURN
    # Returns the raw transition signal if no explicit or default transition mapping is found.
    if transition_signal is not None:
        report_status(
            state="warn",
            message=(
                f"No transition mapping or default for signal {transition_signal!r}; "
                "returning raw signal."
            ),
            context=LogContext(
                component="pompt_engine",
                log_path=log_path,
                trace_id="interface.pompt_engine",
                actor=context.get("user"),
                payload={
                    "transition_signal": transition_signal,
                    "available_transitions": list(transitions.keys()),
                },
            ),
        )
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
        condition: Callable[[dict[str, Any]], bool] | None = None,
    ) -> None:
        """
        Registers a non-linear workflow execution step, specifying its unique key, display label,
        execution handler callback, operating mode, and optional condition predicate.

        Args:
            key (str): The unique identifier key for the workflow step.
            handler (Callable[..., tuple[str | None, dict[str, Any]]]): The callable execution handler
                for the step, returning a next-step target indicator and updated context dictionary.
            label (str | None): The human-readable display label for the workflow step.
            mode (str, optional): The execution mode for the step (e.g., "interactive", "batch").
                Defaults to "interactive".
            condition (Callable[[dict[str, Any]], bool] | None, optional): Optional predicate evaluated
                against runtime context. Defaults to None.
        """
        # STEP REGISTRATION DELEGATION
        # Delegate registration, metadata validation, and storage of the workflow step
        # to the centralized register_step utility, passing the internal steps registry and parameters.
        register_step(self.steps, key, label, handler, mode, condition=condition)

    # WORKFLOW SUBSYSTEM: GRAPH WORKFLOW EXECUTION ENTRY POINT
    # This method serves as the main entry point for graph-based workflow execution,
    # resolving initial state configurations and delegating workflow loop orchestration to modular helpers.
    def execute_workflow(
        self,
        run_key: str,
        workflow_config: dict[str, Any],
        state_context: dict[str, Any],
        registry: dict[str, Any],
    ) -> tuple[bool, dict[str, Any]]:
        """
        Main entry point for graph workflow execution. Resolves initial states from configuration
        and delegates orchestration loop execution to modular helper functions.

        Args:
            run_key (str): The unique run key identifying the workflow execution configuration.
            workflow_config (dict[str, Any]): The workflow configuration dictionary containing states and rules.
            state_context (dict[str, Any]): The current runtime context dictionary carrying execution state.
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
            report_status(
                state="fail",
                message=(
                    f"Workflow execution aborted for run key {run_key!r}: "
                    "missing run definition or initial state."
                ),
                context=LogContext(
                    component="pompt_engine",
                    log_path=log_path,
                    trace_id="interface.pompt_engine",
                    actor=context.get("user"),
                    payload={
                        "run_key": run_key,
                        "has_run_def": bool(run_def),
                        "has_initial_state": bool(current_state_key),
                    },
                ),
            )
            return False, registry

        # WORKFLOW LOOP EXECUTION DELEGATION
        # Delegate the core graph execution loop to the centralized _execute_workflow_loop utility,
        # passing state definitions, current state key, registered steps, state context, and registry.
        return _execute_workflow_loop(
            states, current_state_key, self.steps, state_context, registry
        )
