import argparse
from typing import Any, Callable

from .constants import report_status, log_path  # type: ignore[import-not-found]
from .exceptions import CommandDispatchError, HandlerNotFoundError  # type: ignore[import-not-found]


# SUBCOMMAND DISPATCH & EXECUTION WRAPPER ENGINE
# This utility manages execution scopes for nested subcommands in the CLI parser.
# By triggering primary subcommand handlers and iterating through active child argument flags
# to dispatch matched nested callbacks, it ensures seamless hierarchical command routing.
# [>] EXECUTING SUBCOMMAND DISPATCH WRAPPER
def subcommand_runner(
    args: argparse.Namespace,
    sub_handlers: dict[str, Callable[[argparse.Namespace], None]],
    sub_conf: Any,
) -> None:
    """
    Encapsulates execution scope for nested subcommands. Executes the explicitly registered subcommand handler
    (if present) and iterates through active child argument flags to trigger matched nested callbacks.

    Args:
        args: Parsed command-line arguments namespace container.
        sub_handlers: Dictionary mapping argument keys to executable callback handlers.
        sub_conf: Configuration container holding metadata and primary handlers for the subcommand.

    Raises:
        CommandDispatchError: If an error occurs during subcommand or nested argument handler invocation.
        HandlerNotFoundError: If a subcommand handler is registered but not callable.
    """
    sub_cmd_name = getattr(args, "subcommand", "unknown")
    report_status(
        state="info",
        message=f"Executing subcommand runner for: {sub_cmd_name!r}",
        silent=True,
        log_path=log_path,
    )

    # SUBCOMMAND BASE HANDLER EXECUTION
    # Triggers the explicit top-level callback assigned to the subcommand entry in the configuration.
    if "handler" in sub_conf:
        primary_handler = sub_conf["handler"]
        if not callable(primary_handler):
            raise HandlerNotFoundError(f"Primary handler for subcommand {sub_cmd_name!r} is not callable.")

        report_status(
            state="item",
            message=f"Invoking primary subcommand handler for {sub_cmd_name!r}",
            silent=True,
            log_path=log_path,
        )
        try:
            primary_handler(args)
        except Exception as err:
            raise CommandDispatchError(f"Error during primary handler execution for subcommand {sub_cmd_name!r}: {err}") from err

    # NESTED FLAG HANDLER DISPATCH LOOP
    # Iterates over child flag handlers registered within the sub-router dispatch map.
    for key, h in sub_handlers.items():
        # RECURSION GUARD: SUBCOMMAND KEY FILTER
        # Prevents redundant re-invocations of the subcommand closure when evaluating namespace flags.
        if key == getattr(args, "subcommand", None):
            continue

        # ACTIVE VALUE EVALUATION & CALLBACK TRIGGER
        # Inspects parsed namespace attributes to trigger valid flag/positional callbacks within the subcommand.
        val = getattr(args, key, None)
        if val is not None and val is not False:
            report_status(
                state="item",
                message=f"Invoking sub-argument handler for key: {key!r} (value={val})",
                silent=True,
                log_path=log_path,
            )
            try:
                h(args)
            except Exception as err:
                raise CommandDispatchError(f"Error during sub-argument handler execution for key {key!r}: {err}") from err
