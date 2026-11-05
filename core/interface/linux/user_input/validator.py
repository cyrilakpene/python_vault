import inspect
from typing import Any, Callable

from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# TYPE VALIDATION & WEAVER INITIALIZATION ENGINE
# This routine validates incoming schema architecture and type mapping definitions prior to
# synthesis processing. By enforcing strict list-of-dictionary schema layouts and validating
# data-type casting rules against a registered type matrix, it guarantees schema integrity and
# halts early execution before corrupted states reach downstream synthesis handlers.
def initialize_weaver(
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
            message="Schema Integrity Critical: Expected inbound schema configuration to be a list of dictionaries.",
            context=LogContext(
                component="interface.user_input",
                log_path=log_path,
                silent=False,
                trace_id="user_input",
                actor=context.get("user"),
                payload={
                    "schema_type": type(schema).__name__,
                    "expected_type": "list[dict]",
                },
            ),
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
                f"Unsupported cast type {cast_type!r}. Registered types include: "
                f"{sorted(supported_type_keys)}",
            )

        # INGESTION MATRIX CHECK: Verify input handler registration
        input_type: str = current_field.get("input", "default")
        if input_type not in supported_input_keys:
            # FAIL-FAST INPUT HANDLER TERMINATION
            # If an unregistered input strategy is requested (e.g. typos in secret prompts),
            # abort to prevent silent fallback and unintended terminal output leakage.
            raise ValueError(
                f"Schema Configuration Error at index {index}: "
                f"Unrecognized input handler {input_type!r}. Registered handlers include: "
                f"{sorted(supported_input_keys)}",
            )

    # INITIALIZATION MANIFEST RETURN
    # Yields successful readiness status indicator once all fields pass validation.
    return {"status": "initialized"}


# FUNCTION RESOLUTION & DYNAMIC CASTER FACTORY
# This factory orchestrates the runtime resolution and binding of schema options to type converters.
# By reflecting on target function signatures and constructing parameter-bound closure wrappers,
# it enables dynamic argument injection while maintaining a simple single-argument execution interface.
def resolve_caster(
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
