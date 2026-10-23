from typing import Any

from .constants import report_status, log_path  # type: ignore[import-not-found]
from .exceptions import InvalidConfigError  # type: ignore[import-not-found]


# ARGUMENT REGISTRATION & PARSER CONFIGURATION ENGINE
# This utility manages argument registration for argparse containers, extracting custom execution handlers,
# filtering non-standard configuration metadata, and configuring positional or optional flag bindings.
# [>] EXECUTING ARGUMENT REGISTRATION
def register_arg(
    container: Any,
    name: str,
    opts: dict[str, Any],
    handlers: dict[str, Any],
    is_positional: bool = False,
) -> None:
    """
    Safely extracts custom handler callbacks and argument flags before injecting configuration options
    directly into argparse containers. Ensures dictionary parameter isolation to prevent argument pollution.

    Args:
        container: The argparse parser or argument group container where the argument is injected.
        name: The name or destination identifier for the argument.
        opts: Dictionary of options and metadata configuring the argument behavior.
        handlers: Dictionary mapping argument names to executable callback handlers.
        is_positional: Boolean flag indicating whether the argument is positional or an optional flag.

    Raises:
        InvalidConfigError: If options structure is invalid or mandatory handler types are violated.
    """
    # HANDLER EXTRACTION & REGISTRATION
    # Checks for an executable callback function assigned to the argument key and records it in the handlers dispatch map.
    handler = opts.get("handler")
    if handler:
        if not callable(handler):
            raise InvalidConfigError(
                f"Handler assigned to {name!r} must be a callable function or method."
            )
        report_status(
            state="info",
            message=f"Handler Bound -> {name!r}",
            silent=True,
            log_path=log_path,
        )
        handlers[name] = handler

    if is_positional:
        # POSITIONAL PARAMETER DICTIONARY CLEANUP
        # Strips non-argparse configuration keys (e.g., 'handler') prior to unpacking options into the positional parser container.
        arg_opts = {k: v for k, v in opts.items() if k != "handler"}
        report_status(
            state="item",
            message=f"Positional Arg Added {name!r}",
            silent=True,
            log_path=log_path,
        )
        try:
            container.add_argument(name, **arg_opts)
        except Exception as err:
            raise InvalidConfigError(
                f"Failed to register positional argument {name!r}: {err}"
            ) from err
    else:
        # OPTIONAL FLAG EXTRACTION & DESTRUCTURING
        # Extracts explicit flag definitions or generates default '--name' flags while filtering out non-argparse configuration metadata.
        flags = opts.get("flags", [f"--{name}"])
        if not isinstance(flags, (list, tuple)):
            raise InvalidConfigError(
                f"'flags' parameter for argument {name!r} must be a list or tuple of flag strings."
            )

        arg_opts = {k: v for k, v in opts.items() if k not in ("flags", "handler")}
        report_status(
            state="item",
            message=f"Optional Flag Added flags={flags} -> dest={name!r}",
            silent=True,
            log_path=log_path,
        )
        try:
            container.add_argument(*flags, dest=name, **arg_opts)
        except Exception as err:
            raise InvalidConfigError(
                f"Failed to register optional argument {name!r} with flags {flags}: {err}"
            ) from err
