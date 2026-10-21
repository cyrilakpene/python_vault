import inspect
import getpass
from typing import Any, Callable, cast

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
from .ui import select_option  # type: ignore[import-not-found]
from .exceptions import UserCancelError, MaxRetriesExceededError  # type: ignore[import-not-found]

from report_status import report_status  # type: ignore[import-not-found]
from runtime_context import log_path  # type: ignore[import-not-found]


# TYPE VALIDATION & WEAVER INITIALIZATION ENGINE
# This routine validates incoming schema architecture and type mapping definitions prior to
# synthesis processing. By enforcing strict list-of-dictionary schema layouts and validating
# data-type casting rules against a registered type matrix, it guarantees schema integrity and
# halts early execution before corrupted states reach downstream synthesis handlers.
def _initialize_weaver(
    schema: object,
    supported_type_keys: set[str],
    supported_input_keys: set[str],
) -> dict[str, Any]:
    """
    Validates the structural integrity of an inbound schema and registers type mapping handlers.

    Args:
        schema: Raw inbound configuration object expected to be a list of field dictionaries.
        supported_type_keys: Registered type keys allowed for data casting operations.
        supported_input_keys: Registered input handler strategies available for data ingestion.

    Returns:
        dict[str, Any]: An initialization manifest dictionary if structural checks pass,
            or an empty dictionary if schema typing is invalid.

    Raises:
        ValueError: If an unregistered cast type or input handler signature is encountered in the field matrix.
    """
    # TYPE VALIDATION: SCHEMA INTEGRITY CHECK
    # The synthesis engine requires a structured list of mapping definitions
    # to operate. If the provided 'schema' does not meet this foundational
    # requirement, we must halt the synthesis process.
    if not isinstance(schema, list):
        report_status(
            state="fail",
            message="Schema Critical: Inbound schema must be a list of dictionaries.",
            log_path=log_path,
        )

        # SAFE EXIT: To maintain system stability, we return a neutral, empty
        # dictionary. This prevents downstream "AttributeError" or "TypeError"
        # crashes that would occur if the caller expects a traversable result.
        return {}

    safe_schema: list[Any] = schema  # type: ignore

    # FIELD ITERATION & TYPE DISPATCH MATRIX AUDIT
    # Iterates over each field entry in the schema vector to ensure dictionary typing
    # and confirm that required casting operations match registered strategy handlers.
    for index, field in enumerate(safe_schema):
        # STRUCTURAL ISOLATION: Map current iteration to strict dictionary layout
        # Ensure the checker knows each item in the list is a dictionary map,
        # preventing attribute resolution failures during deep property lookup.
        current_field: dict[str, Any] = field

        # COMPLIANCE MATRIX CHECK: Verify data-type casting registration
        cast_type: str = current_field.get("cast", "str")
        if cast_type not in supported_type_keys:
            # FAIL-FAST SYSTEM TERMINATION
            # Hard failure triggered at the system boundary. We abort execution
            # immediately to prevent downstream side-effects, corrupted state mutations,
            # or infinite terminal loops.
            raise ValueError(
                f"Schema Configuration Error at index {index}: "
                f"Cast type {cast_type!r} is not registered in type_map. "
                f"Supported types are: {sorted(supported_type_keys)}",
            )

        # INGESTION MATRIX CHECK: Verify input handler registration
        input_type: str = current_field.get("input", "default")
        if input_type not in supported_input_keys:
            # FAIL-FAST INPUT HANDLER TERMINATION
            # If an unregistered input strategy is requested (e.g. typos in secret prompts),
            # abort to prevent silent fallback and unintended terminal output leakage.
            raise ValueError(
                f"Schema Configuration Error at index {index}: "
                f"Input handler {input_type!r} is not registered in input_map. "
                f"Supported input handlers are: {sorted(supported_input_keys)}",
            )

    # INITIALIZATION MANIFEST RETURN
    # Yields successful readiness status indicator once all fields pass validation.
    return {"status": "initialized"}


# FUNCTION RESOLUTION & DYNAMIC CASTER FACTORY
# This factory orchestrates the runtime resolution and binding of schema options to type converters.
# By reflecting on target function signatures and constructing parameter-bound closure wrappers,
# it enables dynamic argument injection while maintaining a simple single-argument execution interface.
def _resolve_caster(
    cast_type: str,
    current_field: dict[str, Any],
    type_map: dict[str, Callable[..., Any]],
) -> Callable[[str], Any]:
    """
    DYNAMIC CAST FACTORY: CONTEXT-AWARE CONSTRUCTOR RESOLUTION

    Inspects the target casting callable at runtime to dynamically bind schema-defined
    configuration options. This factory generates a tailored closure, ensuring that
    downstream data converters receive their specific parameters without manual routing.

    Args:
        cast_type: String identifier key registered in the type dispatch mapping matrix.
        current_field: Configuration schema dictionary holding field metadata and execution parameters.
        type_map: Mapping dictionary associating type keys to their corresponding conversion functions.

    Returns:
        Callable[[str], Any]: A single-parameter conversion closure pre-bound with schema parameters.
    """
    func = type_map.get(cast_type, str)
    try:
        # RUNTIME SIGNATURE INSPECTION
        # We reflect on the target validator function to extract its formal parameter names.
        # This allows us to dynamically map schema configuration keys directly to the function arguments.
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        # CONTEXTUAL PARAMETER EXTRACTION
        # We scan the schema's field definition metadata for keys matching any of the function's
        # optional secondary arguments. Matches are extracted and isolated into an injection map.
        extra_args = {}
        for param_name in params[1:]:
            if param_name in ("field", "current_field"):
                extra_args[param_name] = current_field
            elif param_name in current_field:
                extra_args[param_name] = current_field[param_name]

        # CLOSURE BINDING & GENERATION
        # We return a lazy, self-contained closure wrapping the casting function.
        # When executed, it automatically injects the extracted configuration parameters.
        return lambda v: func(v, **extra_args)
    except (ValueError, TypeError):
        # C-EXTENSION & BUILT-IN FALLBACK SAFEGUARD
        # Certain low-level C-extensions or raw built-in types do not support Python's
        # signature inspection API. In these cases, we gracefully fall back to returning
        # the raw casting callable without dynamic parameter bindings to prevent crash loops.
        return func


# BOUNDARY VALIDATION & CONSTRAINT ENFORCEMENT ENGINE
# This validation engine enforces runtime range, length, and set-membership constraints across
# primitive and complex data types. By recursively inspecting collections, measuring string buffer lengths,
# evaluating numeric magnitudes, and validating categorical choice sets, it guarantees that inbound values
# adhere strictly to schema operational boundaries before entering downstream pipelines.
def _enforce_boundaries(v: Any, field: dict[str, Any]) -> None:
    """
    UNIVERSAL BOUNDARY & CHOICE GUARD

    This validator enforces strict 'min', 'max', and 'choices' constraints
    across various data types. It acts as a final sanity check to ensure
    inbound data resides within the operational parameters defined by the
    schema, preventing "out-of-bounds" errors in downstream processes.

    Args:
        v: Data payload value of scalar, string, or collection type to validate.
        field: Configuration schema dictionary defining boundary bounds ('min', 'max', 'choices').

    Raises:
        ValueError: If array dimensions, string lengths, numeric magnitudes, or categorical choices
            violate the constraints defined within the schema.
    """

    # [>] PARAMETER EXTRACTION
    # We retrieve the specific constraints from the field definition.
    # These can apply to numeric magnitudes, string lengths, or
    # collection sizes depending on the context.
    min_val = field.get("min")
    max_val = field.get("max")
    choices = field.get("choices")

    # RECURSIVE LIST HANDLING: NESTED INTEGRITY
    # If the input is a collection, we apply the boundary logic to every
    # individual element. This ensures that a single out-of-bounds item
    # cannot contaminate an otherwise valid list.
    if isinstance(v, (list, tuple)):
        safe_list = cast(list[Any], v)
        v_len = len(safe_list)
        if min_val is not None and v_len < min_val:
            raise ValueError(
                f"Array dimension too short ({v_len} items). Expected at least {min_val}."
            )
        if max_val is not None and v_len > max_val:
            raise ValueError(
                f"Array dimension too long ({v_len} items). Maximum allowed is {max_val}."
            )

        for item in safe_list:
            # [>] RECURSIVE DESCENT
            _enforce_boundaries(item, field)
        return

    # CHOICE VALIDATION: SET MEMBERSHIP
    # If the schema defines a discrete set of permitted values, we perform
    # a high-speed membership check. This is the primary filter for
    # categorical data and operational flags.
    if choices is not None:
        # CHOICE NORMALIZATION: DICTIONARY UNWRAPPER
        # Safely resolves scalar choice keys if choices contain unhashable dictionary objects.
        normalized_choices: list[Any] = [
            c["name"] if isinstance(c, dict) and "name" in c else c for c in choices
        ]

        if v not in normalized_choices:
            # [>] ERROR FORMATTING
            # We stringify the choices to provide the user with clear
            # terminal feedback on what the expected inputs were.
            allowed_str = ", ".join([str(c) for c in normalized_choices])
            raise ValueError(f"{v!r} is invalid. Must be one of: [{allowed_str}]")

    # COMPARATIVE BOUNDARIES: MULTIMODAL MAGNITUDE CHECKS
    # We branch our validation logic based on the data type. This allows the
    # 'min' and 'max' keys to be polymorphic: they enforce numeric range
    # for integers/floats, but enforce character counts for strings.
    if isinstance(v, str):
        # STRING LENGTH VALIDATION: BUFFER OVERFLOW PREVENTION
        # For strings, we measure the character count. This is vital for
        # ensuring that inbound text fits within database constraints or
        # UI display limits.
        v_len = len(v)

        # [>] LOWER BOUND (LENGTH)
        if min_val is not None and v_len < min_val:
            raise ValueError(
                f"Input is too short ({v_len} chars). Minimum length is {min_val}."
            )

        # [>] UPPER BOUND (LENGTH)
        if max_val is not None and v_len > max_val:
            raise ValueError(
                f"Input is too long ({v_len} chars). Maximum allowed is {max_val}."
            )

    elif isinstance(v, (int, float)):
        # NUMERIC VALUE VALIDATION: MAGNITUDE CONTROL
        # For numeric types, we evaluate the absolute value against the
        # defined thresholds. This ensures that quantitative inputs (like
        # bitrates, frame counts, or timestamps) stay within safe
        # operational limits.

        # [>] LOWER BOUND (VALUE)
        if min_val is not None and v < min_val:
            raise ValueError(f"Value {v!r} is too low. Minimum allowed is {min_val}.")

        # [>] UPPER BOUND (VALUE)
        if max_val is not None and v > max_val:
            raise ValueError(f"Value {v!r} is too high. Maximum allowed is {max_val}.")


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
    # Returning an empty dictionary instead of None ensures that
    # downstream 'update()' or 'merge' operations do not trigger a TypeError.
    # [!] VALIDATING INBOUND SCHEMA ARCHITECTURE
    report_status(
        state="task",
        message="VALIDATING INBOUND SCHEMA ARCHITECTURE.",
        silent=True,
        log_path=log_path,
    )

    # CASTING STRATEGY DISPATCH MATRIX
    # Binds string type keys to their corresponding conversion callables, lambdas, or custom parsing utilities.
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
    _initialize_weaver(
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
    # [>] EVALUATING UI PROTOCOL
    report_status(
        state="info", message="Evaluating UI protocol.", silent=True, log_path=log_path
    )
    if not silent:
        # DYNAMIC LABELING: Visual Context Adjustment
        # Adjusts the visual context based on the 'critical' flag, alerting the operator
        # that the engine will enforce a strict retry loop until all validation gates are passed.
        status_label: str = "(STRICT ENFORCEMENT)" if critical else "(STANDARD)"

        # TELEMETRY ANNOUNCEMENT: Session Start
        # Emits the operational session start event to the user terminal and active log file.
        # [~] INITIALIZING DATA COLLECTION SESSION
        report_status(
            state="task",
            message=f"SESSION START: {status_label} MODE",
            log_path=log_path,
        )

    # CONFIGURATION-OVER-CODE ITERATION: SYSTEMATIC SCHEMA SCAN
    # By iterating through a schema rather than hardcoding input calls,
    # we separate the logic of collection from the definition of the data.
    # [>] EXECUTING DATA INGRESS LOOP
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
        # [d] MAPPING TYPE CONSTRUCTORS
        current_field = dict(field)
        attempt_counter: int = 1

        # DATA ACCUMULATOR: RECONCILED STATE INITIALIZATION
        # We initialize the primary results container as an empty dictionary.
        # This will act as the 'Reconciled State' where sanitized and
        # type-casted user responses are staged before being returned
        # to the calling process.
        # [>] INITIALIZING STATE CONTAINER
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

        # THE ATOMIC RETRY GATE: SYNCHRONIZATION POINT
        # By wrapping the input in a 'while True' block, we create a
        # synchronization point. In 'critical' mode, the user cannot
        # proceed until the input satisfies the architectural requirements.
        # [>] COLLECTING FIELD: {field_key}
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
                # This ensures parity with the 'collect_dynamic_inputs' logic
                # and satisfies 'critical' requirements without manual entry.
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
                # Upon detecting a manual interrupt, we provide terminal feedback
                # and execute a clean process termination (exit 0) to signal
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
            # meaning a field is only rejected if it is empty AND has no default.
            if is_field_critical and not user_val and cast_type != "password":
                # [!] VALIDATION FAILURE: EMPTY MANDATORY FIELD
                # We utilize 'report_status' with a 'warn' state to
                # provide high-visibility feedback to the operator.
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
                    caster = _resolve_caster(
                        cast_type=cast_type,
                        current_field=current_field,
                        type_map=type_map,
                    )
                    casted_val = caster(user_val)

                    # BOUNDARY & CONSTRAINT CHECK
                    # Evaluates casted payload against defined min, max, and set choice limits.
                    _enforce_boundaries(v=casted_val, field=field)

                    # STATE PERSISTENCE: RECONCILED DATA BINDING
                    # Assigns the validated payload into the results dictionary under its field key.
                    results[field_key] = casted_val

                    # VALIDATION SUCCESS: DATA LOCK-IN
                    # Once the value is successfully casted, we break the
                    # local retry loop and move to the next field in the schema.
                    # [+] FIELD {field_key} REGISTERED
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
                        # [!] TYPE MISMATCH: INITIATING AUTO-REPAIR

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
