from typing import Literal, TypeAlias

# TYPE DEFINITION: SYMBOLIC STATE MAPPING
# Defines the exhaustive set of valid status keys. Using a TypeAlias
# ensures static analysis tools can validate state transitions at
# development time, reducing runtime errors caused by typos.
StatusState: TypeAlias = Literal[
    "task",
    "info",
    "log_info",
    "warn",
    "item",
    "done",
    "fail",
    "input",
    "debug",
    "proc",
]

# TYPE DEFINITION: LOG SEVERITY MAPPING
# Defines the exhaustive set of valid severity levels supported by the
# structured logging engine, aligned with enterprise log levels.
LogSeverity: TypeAlias = Literal[
    "DEBUG",
    "INFO",
    "NOTICE",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
]

# TYPE DEFINITION: LOG FORMAT MAPPING
# Defines the supported output formatting modes for session logs.
LogFormat: TypeAlias = Literal[
    "structured",
    "legacy",
]

# LOCALIZED SYMBOLIC MAPPING: ENCAPSULATED STATUS INDICATORS
# We define the status indicators within the function scope to enforce
# encapsulation. This ensures the 'Business Logic' of the reporter
# remains self-contained and prevents unintended side-effects in
# the broader application state.
STATUS_MAP: dict[str, str] = {
    "task": "[>]",
    "info": "[~]",
    "log_info": " [~]",
    "warn": "[!]",
    "item": "  [-]",
    "done": "[+]",
    "fail": "[x]",
    "input": "[?]",
    "debug": " [d]",
    "proc": "[#]",
}


# SEVERITY RANKING MAPPING: NUMERIC THRESHOLD WEIGHTS
# Maps standard enterprise log severity names to hierarchical numeric weights,
# enabling fine-grained filtering and threshold evaluations via min_severity gates.
SEVERITY_LEVELS: dict[str, int] = {
    "DEBUG": 10,
    "INFO": 20,
    "NOTICE": 25,
    "SUCCESS": 27,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

# STATUS SYMBOL TO SEVERITY MAPPING
# Maps status indicator symbols to standardized enterprise severity levels.
SEVERITY_MAP: dict[str, str] = {
    ">": "NOTICE",
    "~": "INFO",
    "!": "WARNING",
    "+": "SUCCESS",
    "x": "ERROR",
    "*": "DEBUG",
    "?": "INPUT",
}
