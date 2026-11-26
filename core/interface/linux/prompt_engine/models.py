from typing import Any, Callable
from dataclasses import dataclass, field

from .constants import StepMode  # type: ignore[import-not-found]


# DATACLASS DEFINITION: WORKFLOW STEP SPECIFICATION
# Encapsulates step metadata, handler callables, execution modes, and optional
# conditional predicates for dynamic workflow registries and state graphs.
@dataclass
class WorkflowStep:
    """
    Encapsulates metadata, handler logic, and execution rules for a workflow step.

    Attributes:
        key (str): Unique identifier key for the pipeline or workflow step.
        handler (Callable[..., tuple[str | None, dict[str, Any]]]): Callable routine executed when the step runs.
        label (str | None): Optional human-readable label displayed in interactive prompts or logs. Defaults to None.
        mode (StepMode): Operational execution mode ("interactive", "automatic", or "batch"). Defaults to "interactive".
        condition (Callable[[dict[str, Any]], bool] | None): Optional predicate evaluated against runtime state context. Defaults to None.
        default (bool): Flag indicating whether this step or option is selected by default. Defaults to False.
        metadata (dict[str, Any]): Optional extensible key-value metadata for routing or display.
    """

    key: str
    handler: Callable[..., tuple[str | None, dict[str, Any]]]
    label: str | None = None
    mode: StepMode = "interactive"
    condition: Callable[[dict[str, Any]], bool] | None = None
    default: bool = False
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])
