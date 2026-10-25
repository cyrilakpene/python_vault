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
from .primitive import parse_bool, validate_path, parse_time_to_seconds  # type: ignore[import-not-found]
from .security import parse_password  # type: ignore[import-not-found]
from .validator import initialize_weaver, resolve_caster  # type: ignore[import-not-found]
from .boundary import enforce_boundaries  # type: ignore[import-not-found]
from .ui import select_option  # type: ignore[import-not-found]
from .exceptions import UserCancelError, MaxRetriesExceededError  # type: ignore[import-not-found]
from .constants import report_status, log_path  # type: ignore[import-not-found]


# ARCHITECTURAL GATEKEEPER: UPGRADED SCHEMA-DRIVEN DATA INGRESS ENGINE
# This engine serves as the primary "Sanitization Firewall" for human-to-machine
# data transfer. By decoupling the data definition (Schema) from the collection
# logic, it ensures that all inbound state changes are validated, casted, and
# normalized before reaching the application's core Business Logic.
def user_input(
    schema: list[dict[str, Any]], silent: bool = False, critical: bool = False
) -> dict[str, Any]:
    """
    Collects and sanitizes user input based on a dynamic architectural schema.
    Implements a 'Retry-Until-Valid' logic gate when 'critical' is active.

    This engine bridges the gap between raw human input and structured system
    requirements by implementing strict validation protocols. The logic for
    how data is collected and casted is governed by the schema list.

    Args:
        schema: A list of dictionaries defining the 'key', 'label', 'type',
                and optional 'default' or 'rules' for each required input.
        silent: Global override; if True, suppresses non-essential feedback
                during the collection process.
        critical: Enforcement flag. If True, the engine will loop indefinitely
                  until valid data is provided for required fields.

    Returns:
        A dictionary (reconciled state) containing the sanitized and
        type-casted user responses.
    """

    # SCHEMA INTEGRITY VERIFICATION: INBOUND ARCHITECTURE GUARD
    # We validate the incoming schema structure before initialization.
    # Returning an empty dictionary instead of None.
    report_status(
        state="task",
        message="VALIDATING INBOUND SCHEMA ARCHITECTURE.",
        silent=True,
        log_path=log_path,
    )

    # CASTING STRATEGY DISPATCH MATRIX
    # Binds string type keys to their corresponding conversion callables,
    # lambdas, or custom parsing utilities.
    type_map: dict[str, Callable[..., Any]] = {
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

    # INPUT PROMPT STRATEGY DISPATCH MATRIX
    # Selects interactive CLI inputs prompts based on field schema directives.
    input_map: dict[str, Callable[[dict[str, Any], str], str]] = {
        "default": lambda _field, prompt: input(f"[?] {prompt}: ").strip(),
        "password": lambda _field, prompt: getpass.getpass(f"[?] {prompt}: ").strip(),
        "select": lambda field, prompt: select_option(prompt, field),
    }

    # SUPPORTED TYPES & INPUT ENGINE KEY REGISTRATION
    # Sets the explicit contract boundaries for acceptable primitive types,
    # composite collection structures, and input modifier flags allowed within the schema.
    supported_type_keys: set[str] = {
        "str",
        "int",
        "float",
        "bool",
        "list_str",
        "list_int",
        "list_float",
        "tuple_str",
        "tuple_int",
        "tuple_float",
        "path",
        "timestamp",
        "password",
    }
    supported_input_keys: set[str] = {"default", "password", "select"}

    # SCHEMA WEAVER INITIALIZATION & MATRIX PRE-FLIGHT
    # Triggers pre-flight validation to inspect fields, check type map compatibility,
    # and guarantee structural integrity before entering the user collection loop.
    initialize_weaver(
        schema=schema,
        supported_type_keys=supported_type_keys,
        supported_input_keys=supported_input_keys,
    )

    # RECONCILED STATE CONTAINER INITIALIZATION
    # Instantiates the output dictionary that will accumulate sanitized and validated
    # key-value pairs throughout the ingress lifecycle.
    results: dict[str, Any] = {}

    # CONDITIONAL HEADER RENDERING: UI SESSION INITIALIZATION
    # By implementing a 'silent' flag, we allow the engine to be invoked
    # recursively or within loops without polluting the terminal UI.
    report_status(
        state="info", message="Evaluating UI protocol.", silent=True, log_path=log_path
    )
    if not silent:
        # DYNAMIC LABELING: Visual Context Adjustment
        # Adjusts the visual context based on the 'critical' flag, alerting the operator
        # that the engine will enforce a strict retry loop until all validation gates are passed.
        status_label: str = "(STRICT ENFORCEMENT)" if critical else "(STANDARD)"

        report_status(
            state="task",
            message=f"SESSION START: {status_label} MODE",
            log_path=log_path,
        )

    # CONFIGURATION-OVER-CODE ITERATION: SYSTEMATIC SCHEMA SCAN
    # By iterating through a schema rather than hardcoding input calls,
    # we separate the logic of collection from the definition of the data.
    report_status(
        state="proc",
        message="Executing data ingress loop...",
        silent=True,
        log_path=log_path,
    )
    for field in schema:
        # TYPE ABSTRACTION & FUNCTIONAL MAPPING: CONSTRUCTION LAYER
        # We define a 'type_map' to bridge the gap between static schema
        # definitions and Python's constructor functions. This allows for
        # 'Functional Mapping' where complex transformations (like CSV parsing
        # for lists) are encapsulated within declarative lambda functions.
        current_field = dict(field)
        attempt_counter: int = 1

        report_status(
            state="item",
            message=f"Mapping type constructors: {len(type_map)} casting rules loaded.",
            silent=True,
            log_path=log_path,
        )

        # PATH RESOLUTION: FIELD METADATA EXTRACTION
        # We resolve the unique 'key' for the result dictionary and
        # the human-readable 'label' for the prompt.
        field_key: str = field.get("key", "unknown")
        field_label: str = field.get("label", field_key)

        # TYPE SPECIFICATION: INBOUND CASTING RESOLUTION
        # We extract the 'cast' target (e.g., 'int', 'bool') which
        # determines which function from our 'type_map' will be
        # invoked for normalization.
        cast_type: str | None = field.get("cast", "str")

        # RESOLVE ENFORCEMENT: OVERRIDE CASCADE
        # Check the field dictionary FIRST. If it's not there,
        # fallback to the global function argument.
        is_field_critical = field.get("critical", critical)

        # INPUT HANDLER SELECTION: INTERACTIVE ROUTER
        # Binds the appropriate user prompt callable (standard input vs. hidden password)
        # using the schema 'input' attribute or falling back to the default handler.
        input_handler = input_map.get(
            field.get("input", "default"), input_map["default"]
        )

        report_status(
            state="info",
            message=f"Collecting field: {field_key!r}.",
            silent=True,
            log_path=log_path,
        )

        # RECONCILIATION & RETRY LOOP: ATOMIC INPUT SYNC POINT
        # Executes an indefinite loop for critical fields, continuously prompting the user
        # until valid, type-casted data is provided or a non-critical fallback is accepted.
        while True:
            current_field["attempt"] = attempt_counter
            # INTERRUPT GUARD: KEYBOARD TERMINATION HANDLING
            # We wrap the physical input call in a try-except block to intercept
            # SIGINT (Ctrl+C) signals. This prevents raw Python tracebacks
            # from polluting the terminal and allows for a graceful exit.
            try:
                # ATOMIC INPUT & WHITESPACE SANITIZATION: HUMAN ERROR FILTERING
                # We perform immediate whitespace stripping to prevent 'Dirty Data'
                # (accidental leading/trailing spaces) from causing downstream
                # validation failures or path resolution errors.
                user_val: str = input_handler(field, field_label)

                # SCHEMA DEFAULT INJECTION: ARCHITECTURAL FALLBACK
                # If the operator provides an empty string (direct 'Enter' keypress),
                # the engine checks the schema for a pre-defined 'default'.
                if not user_val and "default" in field:
                    # We cast the default to string to ensure it enters the
                    # Type Conversion firewall in a predictable state.
                    user_val = str(field.get("default"))

                    # FALLBACK TELEMETRY LOGGING
                    # Records the automatic schema default application event to session trace logs.
                    report_status(
                        state="info",
                        message=f"Empty input: Applying schema default {user_val!r}.",
                        silent=True,
                        log_path=log_path,
                    )

            except KeyboardInterrupt:
                # SYMBOLIC EXIT: SIGNALING OPERATOR CANCELLATION
                # Upon detecting a manual interrupt, we raise UserCancelError exception to signal
                # to the shell that the session was ended intentionally.
                print("\n")
                report_status(
                    state="warn",
                    message=str(UserCancelError()),
                    log_path=log_path,
                )
                raise UserCancelError from None

            # MANDATORY PRESENCE VALIDATION: LOGIC BLOCKER
            # If 'critical' is enabled, we treat an empty string as a
            # 'Logic Blocker'. This check occurs AFTER default resolution,
            # meaning a field is only rejected if it is empty AND has no default AND if the 'cast_type' is 'password'.
            if is_field_critical and not user_val and cast_type != "password":
                report_status(
                    state="warn",
                    message=f"Input rejected: {field_label!r} cannot be null in critical mode.",
                    log_path=log_path,
                )

                # RECURSIVE ATTEMPT: We restart the loop for this field
                # to ensure the 'Sanitization Firewall' is not bypassed.
                continue

            # INTEGRITY FIREWALL: TYPE VALIDATION LAYER
            # This section ensures 'Type Safety' at the point of entry.
            # If a field expects a specific primitive or collection, it is
            # guaranteed to be transformed or defaulted before being registered.
            # [>] EXECUTING TYPE CONVERSION
            if cast_type is not None:
                report_status(
                    state="info",
                    message=f"Type conversion: Attempting cast to {cast_type!r}.",
                    silent=True,
                    log_path=log_path,
                )

            # DISPATCH MATRIX EVALUATION & TYPE CASTING EXECUTION
            # Checks if the specified cast strategy exists within the registered type map
            # and attempts dynamic parameter injection and constraint enforcement.
            if cast_type in type_map:
                try:
                    # DYNAMIC TYPE CONVERSION EXECUTION: FUNCTIONAL MAPPING
                    # We invoke the mapped constructor from 'type_map'. This
                    # is where raw strings are transformed into validated
                    # integers, floats, or structured lists.
                    caster = resolve_caster(
                        cast_type=cast_type,
                        current_field=current_field,
                        type_map=type_map,
                    )
                    casted_val = caster(user_val)

                    # BOUNDARY & CONSTRAINT CHECK
                    # Evaluates casted payload against defined min, max, and set choice limits.
                    enforce_boundaries(v=casted_val, field=field)

                    # STATE PERSISTENCE: RECONCILED DATA BINDING
                    # Assigns the validated payload into the results dictionary under its field key.
                    results[field_key] = casted_val

                    report_status(
                        state="item",
                        message=f"Field {field_key!r} registered.",
                        silent=True,
                    )
                    break
                except MaxRetriesExceededError as e:
                    # HARD FAILURE: Immediately crash/halt when max authentication retries are reached
                    report_status(
                        state="fail",
                        message=str(e),
                        log_path=log_path,
                    )
                    # Signal lockout explicitly and abort remaining schema fields immediately
                    results["__status__"] = "MAX_RETRIES_EXCEEDED"
                    return results

                except (ValueError, TypeError) as e:
                    # CONDITIONAL DEGRADATION LOGIC: ARCHITECTURAL FAIL-SAFE
                    # In 'Standard' mode, we favor flow over accuracy by
                    # providing logical defaults. In 'Critical' mode, we
                    # favor accuracy over flow by forcing a re-entry.
                    # [>] HANDLING CASTING EXCEPTION
                    attempt_counter += 1

                    # RETRY ATTEMPT TRACKING TELEMETRY
                    # Logs the retry counter increment event following a conversion exception.
                    report_status(
                        state="info",
                        message="Handling casting exception.",
                        silent=True,
                        log_path=log_path,
                    )

                    if is_field_critical or cast_type == "password":
                        # [x] CASTING FAILURE: STRICT MODE REJECTION
                        # In high-integrity environments, we do not permit
                        # 'Dirty Data' to pass the firewall.
                        error_msg = (
                            str(e)
                            if str(e)
                            else f"{user_val!r} cannot be cast to {cast_type!r}. REJECTING."
                        )

                        # ERROR ANNOUNCEMENT
                        # Displays the exception reason to the operator and prompts for immediate retry.
                        report_status(
                            state="warn", message=error_msg, log_path=log_path
                        )
                        # RE-SYNCHRONIZATION: Forcing the operator back to
                        # the start of the field input loop.
                        continue
                    else:
                        # DYNAMIC REPAIR & CIRCUIT BREAKER: FLOW PRIORITY
                        # We utilize membership testing ('in') to prioritize the
                        # schema-defined 'default'. This ensures that 'None', '0',
                        # or 'False' are respected as intentional architectural
                        # states rather than being treated as 'missing' data.
            
                        if "default" in field:
                            # [~] REPAIRING STATE: Utilizing Explicit Schema Default
                            # By retrieving the value directly, we preserve 'None'
                            # (e.g., for standard episode parts) as valid data.
                            results[field_key] = field.get("default")
                            repair_msg = f"Cast failure. Utilizing explicit default: {results[field_key]!r}."
                        else:
                            # [~] REPAIRING STATE: Utilizing Architectural Constants
                            # If no schema instructions exist, we apply a safe fallback
                            # based on the expected cast type to prevent system drift.
                            results[field_key] = (
                                [] if cast_type and "list" in cast_type else None
                            )
                            repair_msg = f"Type mismatch: No default defined. Fallback to: {results[field_key]!r}."

                        # NON-CRITICAL REPAIR TELEMETRY LOGGING
                        # Emits a warning log detailing the applied fallback default value.
                        report_status(
                            state="warn", message=repair_msg, log_path=log_path
                        )
                        break

    # DATA INGRESS COMPLETE: RECONCILED STATE RETURN
    # After the schema iteration and validation cycles are complete,
    # we return the finalized results dictionary. This represents
    # the 'Truth' that the rest of the application will now consume.
    # [+] RECONCILED STATE READY
    report_status(
        state="done", message="RECONCILED STATE READY.", silent=True, log_path=log_path
    )
    return results
