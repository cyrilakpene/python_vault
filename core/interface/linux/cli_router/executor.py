import argparse
from typing import Any, Callable

from .constants import report_status, log_path  # type: ignore[import-not-found]
from .exceptions import CommandDispatchError, HandlerNotFoundError  # type: ignore[import-not-found]


# ROOT EXECUTION GATE & COMMAND DISPATCHING ENGINE
# This utility manages top-level command-line argument parsing and control flow routing.
# By evaluating parsed namespace values against registered subcommands and argument handlers,
# it dispatches appropriate callback functions or falls back to default handlers and help text.
# [>] EXECUTING ROOT EXECUTION GATE
def handle_root_execution(
    parser: argparse.ArgumentParser,
    config: dict[str, Any],
    handlers: dict[str, Callable[..., Any]],
) -> dict[str, Callable[..., Any]]:
    """
    Parses command line inputs at the root level and routes control flow to matching subcommand or argument handlers.

    Args:
        parser: The fully configured argparse parser instance.
        config: Configuration dictionary holding global parser options and fallback handlers.
        handlers: Dictionary mapping subcommand and argument names to executable callback handlers.

    Returns:
        dict[str, Callable[..., Any]]: The dictionary of registered callback handlers after execution dispatch.

    Raises:
        CommandDispatchError: If an unexpected failure occurs during handler execution.
        HandlerNotFoundError: If a non-callable default handler is assigned.
    """
    report_status(
        state="info",
        message="Parsing command line arguments...",
        silent=True,
        log_path=log_path,
    )

    # CLI ARGUMENT PARSING
    # Evaluates raw command line input (`sys.argv`) against the complete constructed argument schema.
    args = parser.parse_args()
    report_status(
        state="info",
        message=f"Parsed Namespace: {args}",
        silent=True,
        log_path=log_path,
    )

    # DISPATCH EXECUTION TRACKING FLAG
    executed: bool = False

    # SUBCOMMAND DISPATCH RESOLUTION
    # Checks if a subcommand handler exists and was invoked by the user.
    sub_cmd: str | None = getattr(args, "subcommand", None)
    if sub_cmd and sub_cmd in handlers:
        report_status(
            state="item",
            message=f"Routing execution to subcommand: {sub_cmd!r}",
            silent=True,
            log_path=log_path,
        )
        # EXECUTE SUBCOMMAND CALLBACK
        # Immediately transfers control flow to the matched subcommand callback using parsed namespace arguments.
        try:
            handlers[sub_cmd](args)
        except Exception as err:
            raise CommandDispatchError(f"Error encountered while executing subcommand handler for {sub_cmd!r}: {err}") from err
        return handlers

    # OPTIONAL & POSITIONAL ARGUMENT DISPATCH LOOP
    # Iterates through active flags/positionals to trigger matching handler callbacks.
    report_status(
        state="info",
        message="Evaluating argument handlers...",
        silent=True,
        log_path=log_path,
    )
    for name, handler in handlers.items():
        # EVALUATE ACTIVE ARGUMENT VALUE
        # Scans parsed namespace attributes to identify populated values or set flags requiring callback execution.
        val: Any = getattr(args, name, None)
        if val is not None and val is not False:
            report_status(
                state="item",
                message=f"Executing handler for argument: {name!r} (value={val})",
                silent=True,
                log_path=log_path,
            )
            # EXECUTE MATCHED HANDLER
            # Invokes the mapped callback with parsed arguments and trips the execution tracking flag.
            try:
                handler(args)
            except Exception as err:
                raise CommandDispatchError(f"Error encountered while executing handler for argument {name!r}: {err}") from err
            executed = True

    # UNMATCHED COMMAND FALLBACK & DEFAULT HANDLER DISPATCH
    # Executes configured default handler callback or falls back to displaying auto-generated terminal help documentation.
    if not executed and not sub_cmd:
        # DEFAULT HANDLER RESOLUTION
        # Checks for an explicit root-level 'default_handler' fallback function before rendering standard CLI help.
        default_handler = config.get("default_handler")
        if default_handler:
            if not callable(default_handler):
                raise HandlerNotFoundError("Configured 'default_handler' is not callable.")
            report_status(
                state="info",
                message="No matching argument handlers tripped. Invoking default_handler.",
                silent=True,
                log_path=log_path,
            )
            # TRIGGER DEFAULT CALLBACK
            # Executes the default fallback handler with parsed argument namespace.
            try:
                default_handler(args)
            except Exception as err:
                raise CommandDispatchError(f"Error encountered while executing 'default_handler': {err}") from err
        else:
            # DISPLAY HELP DOCUMENTATION
            # Prints auto-generated argument parser usage instructions to terminal.
            report_status(
                state="warn",
                message="No handlers matched and no default_handler found. Rendering help documentation:",
                silent=True,
                log_path=log_path,
            )
            parser.print_help()

    return handlers
