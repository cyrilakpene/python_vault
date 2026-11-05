from typing import Any, Callable

from .validator import initialize_weaver, resolve_caster  # type: ignore[import-not-found]
from .boundary import enforce_boundaries  # type: ignore[import-not-found]
from .exceptions import UserCancelError, MaxRetriesExceededError  # type: ignore[import-not-found]
from .constants import (
    TYPE_MAP,  # type: ignore[import-not-found]
    INPUT_MAP,  # type: ignore[import-not-found]
    SUPPORTED_TYPE_KEYS,  # type: ignore[import-not-found]
    SUPPORTED_INPUT_KEYS,  # type: ignore[import-not-found]
    report_status,  # type: ignore[import-not-found]
    LogContext,  # type: ignore[import-not-found]
    context,  # type: ignore[import-not-found]
    log_path,  # type: ignore[import-not-found]
)


# INGRESS PROCESSING SUBSYSTEM: RAW INPUT FETCHING & CANCELLATION HANDLER
# This utility fetches raw terminal inputs via input handlers, applies schema defaults when inputs are empty,
# intercepts keyboard interruptions, and raises controlled user cancellation errors.
# [>] EXECUTING RAW INPUT FETCHER
def _fetch_raw_input(
    field: dict[str, Any], field_label: str, input_handler: Callable[..., str]
) -> str:
    """
    Fetches raw terminal input and handles schema default injection or cancellation signals.

    Args:
        field (dict[str, Any]): The field configuration schema dictionary.
        field_label (str): The descriptive label for the input field prompt.
        input_handler (Callable[..., str]): The callable handler responsible for acquiring raw input.

    Returns:
        str: The raw user input string or the injected default value.
    """
    try:
        # RAW TERMINAL INPUT ACQUISITION
        # Invokes the input handler to retrieve raw string input from the user or terminal.
        user_val: str = input_handler(field, field_label)

        # EMPTY INPUT DEFAULT INJECTION
        # Checks if input is empty and a non-None default value is defined in the schema, applying it silently.
        if not user_val and "default" in field:
            default_val = field.get("default")
            if default_val is not None:
                user_val = str(default_val)
                report_status(
                    state="info",
                    message=f"Empty input: Applying schema default {user_val!r}.",
                    context=LogContext(
                        component="interface.user_input",
                        log_path=log_path,
                        silent=True,
                        trace_id="user_input",
                        actor=context.get("user"),
                        payload={
                            "field_key": field.get("key"),
                            "default_applied": user_val,
                        },
                    ),
                )
        return user_val

    except KeyboardInterrupt:
        # KEYBOARD INTERCEPTION & CANCELLATION HANDLING
        # Handles user interrupt signals by printing a newline, logging a cancellation warning,
        # and raising UserCancelError.
        print("\n")
        report_status(
            state="warn",
            message=str(UserCancelError()),
            context=LogContext(
                component="interface.user_input",
                log_path=log_path,
                silent=False,
                trace_id="user_input",
                actor=context.get("user"),
                exception=str(UserCancelError()),
                payload={"field_key": field.get("key")},
            ),
        )
        raise UserCancelError from None


# INGRESS PROCESSING SUBSYSTEM: FIELD CASTING & BOUNDARY ENFORCEMENT
# This utility resolves type casting strategies, executes type conversion via type map lookups,
# enforces structural and value boundaries on casted values, and returns validated inputs.
# [>] EXECUTING FIELD CASTING PROCESSOR
def _process_field_casting(
    user_val: str,
    cast_type: str | None,
    current_field: dict[str, Any],
    field: dict[str, Any],
) -> Any:
    """
    Resolves type casting strategy and enforces structural/value boundaries.

    Args:
        user_val (str): The raw user input value to cast.
        cast_type (str | None): The target type casting string descriptor, or None.
        current_field (dict[str, Any]): The current field state dictionary.
        field (dict[str, Any]): The full field configuration schema dictionary.

    Returns:
        Any: The successfully casted and boundary-enforced value, or the original user value.
    """
    # CASTING ATTEMPT NOTIFICATION
    # Reports a silent info status indicating the start of a type conversion attempt.
    if cast_type is not None:
        report_status(
            state="info",
            message=f"Type conversion: Attempting cast to {cast_type!r}.",
            context=LogContext(
                component="interface.user_input",
                log_path=log_path,
                silent=True,
                trace_id="user_input",
                actor=context.get("user"),
                payload={"field_key": field.get("key"), "cast_type": cast_type},
            ),
        )

    # TYPE MAP LOOKUP & CASTER RESOLUTION
    # Resolves and executes the appropriate caster function if the cast type exists within the type map,
    # then enforces structural and value boundaries.
    if cast_type in TYPE_MAP:
        caster = resolve_caster(
            cast_type=cast_type,
            current_field=current_field,
            type_map=TYPE_MAP,
        )
        casted_val = caster(user_val)
        enforce_boundaries(v=casted_val, field=field)
        return casted_val

    # FALLBACK RAW VALUE RETURN
    # Returns the original user value uncasted if no matching cast type is registered.
    return user_val


# INGRESS PROCESSING SUBSYSTEM: FIELD FAILURE & EXCEPTION HANDLER
# This utility manages strict-mode exceptions, incrementing retry counters, handling critical field rejections,
# and assigning safe default or null fallbacks for non-critical failures.
# [>] EXECUTING FIELD FAILURE HANDLER
def _handle_field_failure(
    results: dict[str, Any],
    field: dict[str, Any],
    field_key: str,
    cast_type: str | None,
    user_val: str,
    error: Exception,
    attempt_counter: int,
    is_field_critical: bool,
) -> tuple[bool, int]:
    """
    Manages strict-mode exceptions, retry counters, and non-critical fallbacks.

    Args:
        results (dict[str, Any]): The mutable results dictionary storing ingress values.
        field (dict[str, Any]): The field configuration schema dictionary.
        field_key (str): The dictionary key corresponding to the field.
        cast_type (str | None): The target casting type string.
        user_val (str): The raw user input value that failed casting.
        error (Exception): The exception raised during casting.
        attempt_counter (int): The current retry attempt counter.
        is_field_critical (bool): Flag indicating whether the field is critical.

    Returns:
        tuple[bool, int]: A tuple containing a boolean flag (indicating whether to continue/retry or reject)
        and the updated attempt counter.
    """
    # MAX RETRIES EXCEPTION CHECK
    # Handles maximum retry exhaustion by logging failure and marking the status.
    if isinstance(error, MaxRetriesExceededError):
        report_status(
            state="fail",
            message=str(error),
            context=LogContext(
                component="interface.user_input",
                log_path=log_path,
                trace_id="user_input",
                actor=context.get("user"),
                exception=str(error),
                payload={"field_key": field_key, "attempts": attempt_counter},
            ),
        )
        results["__status__"] = "MAX_RETRIES_EXCEEDED"
        return False, attempt_counter

    # RETRY INCREMENT & CASTING EXCEPTION LOGGING
    # Increments the attempt counter and reports the casting exception event silently.
    attempt_counter += 1
    report_status(
        state="info",
        message="Handling casting exception.",
        context=LogContext(
            component="interface.user_input",
            log_path=log_path,
            silent=True,
            trace_id="user_input",
            actor=context.get("user"),
            exception=str(error),
            payload={"field_key": field_key, "attempt": attempt_counter},
        ),
    )

    # CRITICAL FIELD & PASSWORD REJECTION HANDLING
    # Rejects critical fields or passwords when casting fails, reporting a detailed warning.
    if is_field_critical or cast_type == "password":
        error_msg = (
            str(error)
            if str(error)
            else f"{user_val!r} cannot be cast to {cast_type!r}. REJECTING."
        )
        report_status(
            state="warn",
            message=error_msg,
            context=LogContext(
                component="interface.user_input",
                log_path=log_path,
                trace_id="user_input",
                actor=context.get("user"),
                exception=str(error),
                payload={"field_key": field_key, "critical": is_field_critical},
            ),
        )
        return True, attempt_counter
    else:
        # NON-CRITICAL FALLBACK ASSIGNMENT & MESSAGING
        # Assigns explicit defaults or appropriate empty/null fallback values for non-critical fields,
        # tailoring the logging message based on whether the default is an intentional None or a cast failure.
        if "default" in field:
            results[field_key] = field.get("default")
            if results[field_key] is None:
                state = "info"
                repair_msg = f"Optional field omitted. Defaulting to: None."
            else:
                state = "warn"
                repair_msg = (
                    f"Cast failure. Utilizing explicit default: {results[field_key]!r}."
                )
        else:
            results[field_key] = [] if cast_type and "list" in cast_type else None
            state = "warn"
            repair_msg = f"Type mismatch: No default defined. Fallback to: {results[field_key]!r}."

        # REPAIR WARNING REPORTING & RETURN
        # Reports the fallback repair action and returns success indicators with the updated counter.
        report_status(
            state=state,
            message=repair_msg,
            context=LogContext(
                component="interface.user_input",
                log_path=log_path,
                trace_id="user_input",
                actor=context.get("user"),
                payload={"field_key": field_key, "fallback_value": results[field_key]},
            ),
        )
        return False, attempt_counter


# CONFIGURATION SUBSYSTEM: DYNAMIC USER INPUT COLLECTION & SCHEMA RECONCILIATION
# This utility collects and sanitizes user input based on a dynamic architectural schema,
# implementing retry-until-valid logic gates, input type casting, and telemetry reporting.
# [>] EXECUTING USER INPUT COLLECTION ENGINE
def user_input(
    schema: list[dict[str, Any]], silent: bool = False, critical: bool = False
) -> dict[str, Any]:
    """
    Collects and sanitizes user input based on a dynamic architectural schema.
    Implements a 'Retry-Until-Valid' logic gate when 'critical' is active.

    Args:
        schema (list[dict[str, Any]]): A list of dictionaries defining the configuration field schemas.
        silent (bool): Flag to suppress standard UI session logs. Defaults to False.
        critical (bool): Flag to enforce strict input validation and retry-until-valid logic gates. Defaults to False.

    Returns:
        dict[str, Any]: A dictionary of collected and casted user input values, including status markers if failed.
    """
    # INBOUND SCHEMA VALIDATION REPORT
    # Reports the start of inbound schema architecture validation silently.
    report_status(
        state="task",
        message="Validating inbound schema architecture.",
        context=LogContext(
            component="interface.user_input",
            log_path=log_path,
            silent=True,
            trace_id="user_input",
            actor=context.get("user"),
            payload={
                "total_fields": len(schema),
            },
        ),
    )

    # WEAVER INITIALIZATION
    # Initializes the configuration weaver with the schema and supported type and input keys.
    initialize_weaver(
        schema=schema,
        supported_type_keys=SUPPORTED_TYPE_KEYS,
        supported_input_keys=SUPPORTED_INPUT_KEYS,
    )

    results: dict[str, Any] = {}

    # UI PROTOCOL EVALUATION REPORT
    # Evaluates UI protocols silently before checking silent mode flags.
    report_status(
        state="info",
        message=f"Evaluating UI protocol. Registry loaded: {len(TYPE_MAP)} type_map and"
        f" {len(INPUT_MAP)} input_type operators available.",
        context=LogContext(
            component="interface.user_input",
            log_path=log_path,
            silent=True,
            trace_id="user_input",
            actor=context.get("user"),
            payload={
                "cast_type_available": list(TYPE_MAP.keys()),
                "input_type_available": list(INPUT_MAP.keys()),
            },
        ),
    )
    if not silent:
        status_label: str = "(STRICT ENFORCEMENT)" if critical else "(STANDARD)"
        report_status(
            state="task",
            message=f"SESSION START: {status_label} MODE",
            context=LogContext(
                component="interface.user_input",
                log_path=log_path,
                silent=False,
                trace_id="user_input",
                actor=context.get("user"),
            ),
        )

    # DATA INGRESS LOOP INITIATION REPORT
    # Reports the initiation of the data ingress loop silently.
    report_status(
        state="proc",
        message="Executing data ingress loop...",
        context=LogContext(
            component="interface.user_input",
            log_path=log_path,
            silent=True,
            trace_id="user_input",
            actor=context.get("user"),
        ),
    )

    # SCHEMA FIELD ITERATION & INGRESS LOOP
    # Iterates over each field in the schema, managing attempt counters, raw fetches, validation, and casting.
    for field in schema:
        current_field = dict(field)
        attempt_counter: int = 1

        field_key: str = field.get("key", "unknown")
        field_label: str = field.get("label", field_key)
        cast_type: str | None = field.get("cast", "str")
        is_field_critical = field.get("critical", critical)
        input_handler = INPUT_MAP.get(
            field.get("input", "default"), INPUT_MAP["default"]
        )

        # FIELD COLLECTION TELEMETRY REPORT
        # Reports the collection status of the current field key silently.
        report_status(
            state="info",
            message=f"Collecting field: {field_key!r}.",
            context=LogContext(
                component="interface.user_input",
                log_path=log_path,
                silent=True,
                trace_id="user_input",
                actor=context.get("user"),
                payload={
                    "field_key": field_key,
                    "critical": is_field_critical,
                },
            ),
        )

        while True:
            current_field["attempt"] = attempt_counter
            user_val = _fetch_raw_input(field, field_label, input_handler)

            # CRITICAL NULL VALUE GUARD
            # Rejects empty user input for critical fields unless the cast type is password.
            if is_field_critical and not user_val and cast_type != "password":
                report_status(
                    state="warn",
                    message=f"Input rejected: {field_label!r} cannot be null in critical mode.",
                    context=LogContext(
                        component="interface.user_input",
                        log_path=log_path,
                        silent=False,
                        trace_id="user_input",
                        actor=context.get("user"),
                        payload={
                            "field_key": field_key,
                            "reason": "null_in_critical_mode",
                        },
                    ),
                )
                continue

            # FIELD CASTING & REGISTRATION
            # Attempts to cast raw user input according to the schema specification and registers the result.
            try:
                casted_val = _process_field_casting(
                    user_val, cast_type, current_field, field
                )
                results[field_key] = casted_val
                report_status(
                    state="item",
                    message=f"Field {field_key!r} registered.",
                    context=LogContext(
                        component="interface.user_input",
                        log_path=log_path,
                        silent=True,
                        trace_id="user_input",
                        actor=context.get("user"),
                        payload={"field_key": field_key, "registered": True},
                    ),
                )
                break
            except (MaxRetriesExceededError, ValueError, TypeError) as e:
                if (
                    isinstance(e, MaxRetriesExceededError)
                    or results.get("__status__") == "MAX_RETRIES_EXCEEDED"
                ):
                    results["__status__"] = "MAX_RETRIES_EXCEEDED"
                    report_status(
                        state="fail",
                        message=str(e),
                        context=LogContext(
                            component="interface.user_input",
                            log_path=log_path,
                            silent=False,
                            trace_id="user_input",
                            actor=context.get("user"),
                            exception=str(e),
                            payload={"field_key": field_key},
                        ),
                    )
                    return results

                # FIELD FAILURE HANDLING & RETRY DELEGATION
                # Delegates field failure handling to evaluate retry attempts or break the loop.
                should_continue, attempt_counter = _handle_field_failure(
                    results,
                    field,
                    field_key,
                    cast_type,
                    user_val,
                    e,
                    attempt_counter,
                    is_field_critical,
                )
                if should_continue:
                    continue
                else:
                    break

    # RECONCILED STATE READY REPORT
    # Reports the successful completion and reconciliation of the user input collection process.
    report_status(
        state="done",
        message="Reconciled state ready.",
        context=LogContext(
            component="interface.user_input",
            log_path=log_path,
            silent=True,
            trace_id="user_input",
            actor=context.get("user"),
            payload={"collected_fields_count": len(results)},
        ),
    )

    # RESULTS DICTIONARY RETURN
    # Returns the finalized dictionary of collected and casted configuration values.
    return results
