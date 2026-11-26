from typing import Literal, TypeAlias

from status_reporter import report_status, LogContext  # type: ignore[import-not-found]
from heuristic_renderer import heuristic_ui_renderer  # type: ignore[import-not-found]
from runtime_pkg import context, log_path  # type: ignore[import-not-found]

# TYPE ALIAS: WORKFLOW STEP EXECUTION MODE
# Defines valid keyword literals for configuring how a workflow step runs.
StepMode: TypeAlias = Literal["interactive", "automatic", "batch"]
