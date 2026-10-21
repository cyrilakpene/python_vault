# SYSTEM INTERRUPTION EXCEPTION CLASS
# Custom exception domain class used to signal explicit user cancellations or interactive abort requests (e.g., SIGINT / Ctrl+C).
# Standardizes cancellation formatting across CLI workflows to enable graceful process termination without stack traces.
class UserCancelError(Exception):
    """Raised when user cancels operation."""

    def __init__(self, message: str = "User interrupted process (Ctrl+C)."):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes cancellation message with standard system tag before delegating to BaseException initializer.
        super().__init__(f"Operation Cancel: {message}")


# RETRY BOUNDARY FAILURE EXCEPTION CLASS
# Custom exception domain class inheriting from ValueError to signal when interactive authentication or field input retries
# breach configured safety limits. Standardizes error output across CLI authentication boundaries to prevent brute-force execution.
class MaxRetriesExceededError(ValueError):
    """Raised when authentication attempts exceed the retry threshold."""

    def __init__(self, message: str = "Maximum attempt limit exceeded."):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes failure message with standard security tag before delegating to ValueError initializer.
        super().__init__(f"Authentication Failure: {message}")
