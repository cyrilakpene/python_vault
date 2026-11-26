from typing import Any, Callable


# SYSTEM UTILITIES SUBSYSTEM: TEMPLATE FORMATTING & CALLABLE DISPATCH
# This utility applies named keyword arguments or positional arguments to string templates
# or callable transformers based on input types and availability.
# [>] EXECUTING FORMAT MATCH
def format_match(
    target: str | Callable[..., str],
    kwargs: dict[str, Any],
    args: tuple[Any, ...],
) -> str:
    """
    Applies named keyword arguments or positional arguments to a string template or callable transformer.

    Args:
        target (str | Callable[..., str]): The string template or callable function to evaluate.
        kwargs (dict[str, Any]): Keyword arguments to pass to the target.
        args (tuple[Any, ...]): Positional arguments to pass to the target.

    Returns:
        str: The formatted string result.
    """
    # CALLABLE TARGET DISPATCH
    # Evaluates the target as a callable transformer using positional and keyword arguments.
    if callable(target):
        return str(target(*args, **kwargs))

    # STRING TEMPLATE FORMATTING
    # Formats the string template target using positional and keyword arguments together.
    return target.format(*args, **kwargs)
