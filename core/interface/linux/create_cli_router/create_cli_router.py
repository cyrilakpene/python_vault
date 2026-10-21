import argparse
from typing import Any, Callable

from interface.report_status import report_status  # type: ignore[import-not-found]
from security.runtime_context import log_path  # type: ignore[import-not-found]


# DYNAMIC CLI ROUTER & ARGPARSE COMMAND DISPATCH ENGINE
# This routing engine dynamically translates structured nested configuration dictionaries into standard
# Python argparse hierarchies. Supporting positional inputs, mutually exclusive flag groups, recursive subcommands,
# and parameter handler callbacks, it resolves incoming arguments into executed commands with automated help rendering.
def create_cli_router(
    config: dict[str, Any],
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
    """
    # ROOT PARSER INITIALIZATION & META-FLAG REGISTRATION
    # Evaluates whether this call forms the root entry point or a nested subcommand recursion branch.
    # Instantiates top-level parser metadata and binds version flag handlers when present.
    is_root: bool = parser is None
    cmd_name: str = config.get("name", "cli")
    if is_root:
        report_status(
            state="info",
            message=f"Initializing root parser for binary: {cmd_name!r}",
            silent=True,
            log_path=log_path,
        )
        # CONSTRUCT BASE PARSER
        # Uses root configuration attributes to set the program binary name and top-level CLI description.
        parser = argparse.ArgumentParser(
            prog=cmd_name, description=config.get("description", "")
        )

        # VERSION FLAG INJECTION
        # Configures programmatic '-v' and '--version' flag handlers if version metadata exists in config.
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

    # HANDLER DISPATCH MATRIX INITIALIZATION
    # Staging dictionary mapping command names and flag destination keys to their callback functions.
    handlers: dict[str, Callable[..., Any]] = {}

    def _register_arg(
        container: Any, name: str, opts: dict[str, Any], is_positional: bool = False
    ) -> None:
        """
        HELPER ARGUMENT REGISTRATION ENGINE

        Safely extracts custom handler callbacks and argument flags before injecting configuration options
        directly into argparse containers. Ensures dictionary parameter isolation to prevent argument pollution.
        """
        # HANDLER EXTRACTION & REGISTRATION
        # Checks for an executable callback function assigned to the argument key and records it in the handlers dispatch map.
        handler = opts.get("handler")
        if handler:
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
            container.add_argument(name, **arg_opts)
        else:
            # OPTIONAL FLAG EXTRACTION & DESTRUCTURING
            # Extracts explicit flag definitions or generates default '--name' flags while filtering out non-argparse configuration metadata.
            flags = opts.get("flags", [f"--{name}"])
            arg_opts = {k: v for k, v in opts.items() if k not in ("flags", "handler")}
            report_status(
                state="item",
                message=f"Optional Flag Added flags={flags} -> dest={name!r}",
                silent=True,
                log_path=log_path,
            )
            container.add_argument(*flags, dest=name, **arg_opts)

    # 1. POSITIONAL ARGUMENT CONFIGURATION & BINDING
    # Iterates over positional specifications, extracting handler callables and registering positional parser bounds.
    for name, opts in config.get("positionals", {}).items():
        # EXTRACT CALLBACK & REGISTER POSITIONAL PARAMETER
        # Isolates optional 'handler' callables from options before unpacking directly into the parser's schema.
        report_status(
            state="info",
            message=f"Registering positionals for {cmd_name!r}...",
            silent=True,
            log_path=log_path,
        )
        _register_arg(container=parser, name=name, opts=opts, is_positional=True)

    # 2. MUTUALLY EXCLUSIVE GROUP INJECTION
    # Creates isolated mutually exclusive groups, mapping alternative command flags to designated destinations.
    for idx, group_specs in enumerate(config.get("mutually_exclusive", []), start=1):
        req = group_specs.get("required", False)
        report_status(
            state="info",
            message=f"Registering mutually exclusive group #{idx} (required={req}) for {cmd_name!r}...",
            silent=True,
            log_path=log_path,
        )
        # GROUP CREATION & FLAG RECONCILIATION
        # Instantiates the mutually exclusive container and binds custom or default dual-dash flag aliases.
        group = parser.add_mutually_exclusive_group(required=req)
        for arg_name, opts in group_specs.get("arguments", {}).items():
            _register_arg(container=group, name=arg_name, opts=opts)

    # 3. STANDARD OPTIONAL ARGUMENT BINDING
    # Processes optional flag definitions, associating flags with destination keys and handler functions.
    for name, opts in config.get("arguments", {}).items():
        report_status(
            state="info",
            message=f"Registering optional arguments for {cmd_name!r}...",
            silent=True,
            log_path=log_path,
        )
        # FLAG EXTRACT & OPTIONAL ARGUMENT REGISTRATION
        # Populates flag definitions into the parser while mapping any detached callbacks to the destination key.
        _register_arg(container=parser, name=name, opts=opts)

    # 4. RECURSIVE SUBCOMMAND TREE CONSTRUCTION
    # Configures nested subcommand action parsers, recursively mapping child router definitions.
    sub_configs: dict[str, Any] = config.get("subcommands", {})
    if sub_configs:
        report_status(
            state="info",
            message=f"Building subcommands tree for {cmd_name!r}: {list(sub_configs.keys())}",
            silent=True,
            log_path=log_path,
        )
        # SUBPARSER CONTAINER INITIALIZATION
        # Attaches subparser functionality under the 'subcommand' destination attribute.
        subparsers_action = parser.add_subparsers(
            dest="subcommand", required=True, help="Available subcommands"
        )
        for sub_name, sub_conf in sub_configs.items():
            # CHILD PARSER GENERATION & RECURSIVE DISPATCH
            # Spawns a dedicated sub-parser instance for each sub-key and recursively collects child handlers.
            sub_parser = subparsers_action.add_parser(
                sub_name, help=sub_conf.get("description", "")
            )
            # Recursively build subcommand structure and collect its handlers
            sub_handlers = create_cli_router(sub_conf, parser=sub_parser)

            def _subcommand_runner(
                args: argparse.Namespace,
                sh: dict[str, Callable[[argparse.Namespace], None]] = sub_handlers,
                sc: Any = sub_conf,
            ) -> None:
                """
                SUBCOMMAND DISPATCH CLOSURE WRAPPER

                Encapsulates execution scope for nested subcommands. Executes the explicitly registered subcommand handler
                (if present) and iterates through active child argument flags to trigger matched nested callbacks.
                """
                report_status(
                    state="info",
                    message=f"Executing subcommand runner for: {args.subcommand!r}",
                    silent=True,
                    log_path=log_path,
                )
                # SUBCOMMAND BASE HANDLER EXECUTION
                # Triggers the explicit top-level callback assigned to the subcommand entry in the configuration.
                if "handler" in sc:
                    report_status(
                        state="item",
                        message=f"Invoking primary subcommand handler for {args.subcommand!r}",
                        silent=True,
                        log_path=log_path,
                    )
                    sc["handler"](args)

                # NESTED FLAG HANDLER DISPATCH LOOP
                # Iterates over child flag handlers registered within the sub-router dispatch map.
                for key, h in sh.items():
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
                        h(args)

            # BIND CLOSURE TO SUBCOMMAND DISPATCH KEY
            # Maps the encapsulated runner function into the primary handlers dictionary using the subcommand name.
            handlers[sub_name] = _subcommand_runner

    # ROOT EXECUTION GATE & COMMAND DISPATCHING
    # Parses command line inputs at the root level and routes control flow to matching subcommand or argument handlers.
    if is_root:
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
            handlers[sub_cmd](args)
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
                handler(args)
                executed = True

        # UNMATCHED COMMAND FALLBACK & DEFAULT HANDLER DISPATCH
        # Executes configured default handler callback or falls back to displaying auto-generated terminal help documentation.
        if not executed and not sub_cmd:
            # DEFAULT HANDLER RESOLUTION
            # Checks for an explicit root-level 'default_handler' fallback function before rendering standard CLI help.
            default_handler = config.get("default_handler")
            if default_handler:
                report_status(
                    state="info",
                    message="No matching argument handlers tripped. Invoking default_handler.",
                    silent=True,
                    log_path=log_path,
                )
                # TRIGGER DEFAULT CALLBACK
                # Executes the default fallback handler with parsed argument namespace.
                default_handler(args)
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

    # DISPATCH MAP RETURN
    # Returns resolved handler registry dictionary for program consumption.
    return handlers
