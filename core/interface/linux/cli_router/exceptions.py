# INVALID CONFIGURATION EXCEPTION CLASS
# Custom exception domain class inheriting from ValueError to signal malformed CLI configuration structures.
# Standardizes error messages when mandatory configuration keys or invalid option parameters are encountered during router initialization.
class InvalidConfigError(ValueError):
    """Raised when the CLI parser configuration schema or options are invalid."""

    def __init__(self, message: str = "Invalid router configuration provided."):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes configuration error message with standard schema tag before delegating to ValueError initializer.
        super().__init__(f"Configuration Error: {message}")


# HANDLER REGISTRATION EXCEPTION CLASS
# Custom exception domain class used to signal missing, invalid, or duplicate callback handlers during CLI tree construction.
# Enforces validation across subcommand and argument handler mappings prior to command dispatch.
class HandlerNotFoundError(Exception):
    """Raised when a specified or expected handler callback is missing or unresolvable."""

    def __init__(self, message: str = "Required callback handler is missing or unresolvable."):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes handler error message with standard dispatch tag before delegating to BaseException initializer.
        super().__init__(f"Handler Dispatch Error: {message}")


# COMMAND DISPATCH EXCEPTION CLASS
# Custom exception domain class inheriting from RuntimeError to handle failure states during argument evaluation or subcommand routing.
# Standardizes execution errors encountered when dispatching control flow across registered CLI nodes.
class CommandDispatchError(RuntimeError):
    """Raised when an error occurs during subcommand or argument handler execution routing."""

    def __init__(self, message: str = "Failed to dispatch command handler."):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes routing failure message with standard execution tag before delegating to RuntimeError initializer.
        super().__init__(f"Execution Failure: {message}")
