import argparse
from typing import Any, Callable, cast

from .helpers import register_arg  # type: ignore[import-not-found]
from .subcommand import subcommand_runner  # type: ignore[import-not-found]
from .executor import handle_root_execution  # type: ignore[import-not-found]
from .constants import report_status, log_path  # type: ignore[import-not-found]
from .exceptions import InvalidConfigError  # type: ignore[import-not-found]


# DYNAMIC CLI ROUTER & ARGPARSE COMMAND DISPATCH ENGINE
# This utility constructs dynamic command-line argument parsers recursively from configuration dictionaries.
# By handling positionals, mutually exclusive groups, optional arguments, and nested subcommands,
# it builds robust CLI trees and routes execution handlers.
# [>] EXECUTING DYNAMIC CLI ROUTER INITIALIZATION
def create_cli_router(
    config: Any,
    parser: argparse.ArgumentParser | None = None,
) -> dict[str, Callable[..., Any]]:
    """
    Enhanced CLI router supporting positionals, mutually exclusive groups,
    nested subcommands, and dynamic handlers with full type hinting.

    Args:
        config: Nested configuration dictionary declaring CLI flags, arguments, subcommands, and handlers.
        parser: Optional top-level or child ArgumentParser instance for recursive command building.

    Returns:
        dict[str, Callable[..., Any]]: Mapping dictionary of argument/command names to their executable handlers.

    Raises:
        InvalidConfigError: If config structure is not a dictionary.
    """
    if not isinstance(config, dict):
        raise InvalidConfigError("CLI configuration must be a dictionary.")

    # ROOT PARSER INITIALIZATION & META-FLAG REGISTRATION
    # Determines if this is the root router instance, initializing the top-level ArgumentParser
    # and registering optional global version flags if configured.
    is_root: bool = parser is None
    config_dict = cast(dict[str, Any], config)
    cmd_name = cast(str, config_dict.get("name", "cli"))
    if is_root:
        report_status(
            state="info",
            message=f"Initializing root parser for binary: {cmd_name!r}",
            silent=True,
            log_path=log_path,
        )
        parser = argparse.ArgumentParser(
            prog=cmd_name, description=cast(str, config_dict.get("description", ""))
        )

        # VERSION FLAG INJECTION
        # Injects standard version flags (-v / --version) into the root parser when specified.
        if "version" in config:
            report_status(
                state="info",
                message=f"Registering version flag (-v / --version) -> {config['version']}",
                silent=True,
                log_path=log_path,
            )
            parser.add_argument(
                "-v",
                "--version",
                action="version",
                version=f"%(prog)s {config['version']}",
            )
    else:
        report_status(
            state="info",
            message=f"Initializing sub-parser for command branch: {cmd_name!r}",
            silent=True,
            log_path=log_path,
        )

    assert parser is not None

    # HANDLER DISPATCH MATRIX INITIALIZATION
    # Allocates the dictionary mapping argument and subcommand names to their executable callback functions.
    handlers: dict[str, Callable[..., Any]] = {}

    # POSITIONAL ARGUMENT CONFIGURATION & BINDING
    # Iterates through configured positional parameters, registering them into the parser container.
    positionals = config_dict.get("positionals", {})
    if not isinstance(positionals, dict):
        raise InvalidConfigError(
            "'positionals' configuration block must be a dictionary mapping names to options."
        )
    positionals = cast(dict[str, Any], positionals)

    for name, opts in positionals.items():
        report_status(
            state="info",
            message=f"Registering positionals for {cmd_name!r}...",
            silent=True,
            log_path=log_path,
        )
        register_arg(
            container=parser,
            name=name,
            opts=opts,
            handlers=handlers,
            is_positional=True,
        )

    # MUTUALLY EXCLUSIVE GROUP INJECTION
    # Creates mutually exclusive argument groups and registers their respective child options.
    mutually_exclusive = config_dict.get("mutually_exclusive", [])
    if not isinstance(mutually_exclusive, list):
        raise InvalidConfigError(
            "'mutually_exclusive' configuration block must be a list of group specs."
        )
    mutually_exclusive = cast(list[Any], mutually_exclusive)

    for idx, group_specs in enumerate(mutually_exclusive, start=1):
        if not isinstance(group_specs, dict):
            raise InvalidConfigError(
                f"Mutually exclusive group specification #{idx} must be a dictionary."
            )

        group_config = cast(dict[str, Any], group_specs)
        req = group_config.get("required", False)
        report_status(
            state="info",
            message=f"Registering mutually exclusive group #{idx} (required={req}) for {cmd_name!r}...",
            silent=True,
            log_path=log_path,
        )
        group = parser.add_mutually_exclusive_group(required=req)
        args_spec = group_config.get("arguments", {})
        if not isinstance(args_spec, dict):
            raise InvalidConfigError(
                f"'arguments' inside mutually exclusive group #{idx} must be a dictionary."
            )

        for arg_name, opts in cast(dict[str, Any], args_spec).items():
            register_arg(container=group, name=arg_name, opts=opts, handlers=handlers)

    # STANDARD OPTIONAL ARGUMENT BINDING
    # Iterates through optional flag configurations and binds them to the parser.
    arguments = config_dict.get("arguments", {})
    if not isinstance(arguments, dict):
        raise InvalidConfigError(
            "'arguments' configuration block must be a dictionary."
        )
    arguments = cast(dict[str, Any], arguments)

    for name, opts in arguments.items():
        report_status(
            state="info",
            message=f"Registering optional arguments for {cmd_name!r}...",
            silent=True,
            log_path=log_path,
        )
        register_arg(container=parser, name=name, opts=opts, handlers=handlers)

    # RECURSIVE SUBCOMMAND TREE CONSTRUCTION
    # Configures subparsers and recursively builds nested command structures for hierarchical CLIs.
    sub_configs = config_dict.get("subcommands", {})
    if not isinstance(sub_configs, dict):
        raise InvalidConfigError(
            "'subcommands' configuration block must be a dictionary."
        )
    sub_configs = cast(dict[str, Any], sub_configs)

    if sub_configs:
        report_status(
            state="info",
            message=f"Building subcommands tree for {cmd_name!r}: {list(sub_configs.keys())}",
            silent=True,
            log_path=log_path,
        )
        subparsers_action = parser.add_subparsers(
            dest="subcommand", required=True, help="Available subcommands"
        )
        for sub_name, sub_conf in sub_configs.items():
            if not isinstance(sub_conf, dict):
                raise InvalidConfigError(
                    f"Subcommand configuration for {sub_name!r} must be a dictionary."
                )

            sub_parser = subparsers_action.add_parser(
                sub_name,
                help=cast(str, cast(dict[str, Any], sub_conf).get("description", "")),
            )
            # Recursively build subcommand structure and collect its handlers
            sub_handlers = create_cli_router(sub_conf, parser=sub_parser)

            # BIND CLOSURE TO SUBCOMMAND DISPATCH KEY
            # Creates a closure wrapper to dispatch execution when the subcommand is invoked.
            def run_subcommand(
                args: argparse.Namespace,
                sh: dict[str, Callable[..., Any]] = sub_handlers,
                sc: dict[str, Any] = sub_conf,
            ) -> Any:
                return subcommand_runner(args, sh, sc)

            handlers[sub_name] = run_subcommand

    # ROOT EXECUTION GATE
    # Invokes the root execution gate if this is the top-level parser invocation.
    if is_root:
        return handle_root_execution(parser, config_dict, handlers)

    # DISPATCH MAP RETURN
    # Returns the populated handler dispatch dictionary for child sub-routers.
    return handlers
