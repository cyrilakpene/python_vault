import getpass
from typing import Any, Callable

from .collective import (
    parse_list_str,  # type: ignore[import-not-found]
    parse_list_int,  # type: ignore[import-not-found]
    parse_list_float,  # type: ignore[import-not-found]
    parse_tuple_str,  # type: ignore[import-not-found]
    parse_tuple_int,  # type: ignore[import-not-found]
    parse_tuple_float,  # type: ignore[import-not-found]
)
from .primitive import (
    parse_bool,  # type: ignore[import-not-found]
    validate_path,  # type: ignore[import-not-found]
    parse_time_to_seconds,  # type: ignore[import-not-found]
)
from .security import parse_password  # type: ignore[import-not-found]
from .ui import select_option  # type: ignore[import-not-found]

from status_reporter import report_status, LogContext  # type: ignore[import-not-found]
from runtime_pkg import context, log_path  # type: ignore[import-not-found]

# CONFIGURATION SUBSYSTEM: TYPE PARSING MAPPING REGISTRY
# This dictionary maps type string identifiers to their respective parsing and validation callables,
# facilitating dynamic string-to-type conversion for command-line arguments, config parsers, and input schemas.
# [>] DEFINING TYPE MAPPING REGISTRY
TYPE_MAP: dict[str, Callable[..., Any]] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": parse_bool,
    "list_str": parse_list_str,
    "list_int": parse_list_int,
    "list_float": parse_list_float,
    "tuple_str": parse_tuple_str,
    "tuple_int": parse_tuple_int,
    "tuple_float": parse_tuple_float,
    "path": validate_path,
    "timestamp": parse_time_to_seconds,
    "password": parse_password,
}

# CONFIGURATION SUBSYSTEM: INPUT STRATEGY MAPPING REGISTRY
# This dictionary maps input method identifiers to lambda callables that handle standard string input,
# secure password masking via getpass, and interactive option selection for configuration schemas.
# [>] DEFINING INPUT STRATEGY MAPPING REGISTRY
INPUT_MAP: dict[str, Callable[[dict[str, Any], str], str]] = {
    # DEFAULT INPUT STRATEGY
    # Prompts the user for standard string input using standard input streams and strips whitespace.
    "default": lambda _field, prompt: input(f"[?] {prompt}: ").strip(),
    # PASSWORD INPUT STRATEGY
    # Prompts the user for masked password input using the getpass utility and strips whitespace.
    "password": lambda _field, prompt: getpass.getpass(f"[?] {prompt}: ").strip(),
    # SELECT INPUT STRATEGY
    # Prompts the user to select an option from a predefined list or menu based on field specifications.
    "select": lambda field, prompt: select_option(prompt, field),
}

# CONFIGURATION SUBSYSTEM: SUPPORTED TYPE AND INPUT KEY SETS
# This module defines validated sets of supported type and input method keys derived from
# registry dictionaries to ensure strict key compliance across configuration validation checks.
# [>] DEFINING SUPPORTED KEY SETS
SUPPORTED_TYPE_KEYS: set[str] = set(TYPE_MAP.keys())
SUPPORTED_INPUT_KEYS: set[str] = {"default", "password", "select"}
