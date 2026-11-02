from typing import Any, Callable


# SYSTEM UTILITIES SUBSYSTEM: TEMPLATE FORMATTING & CALLABLE DISPATCH
# This utility applies named keyword arguments or positional arguments to string templates
# or callable transformers based on input types and availability.
# [>] EXECUTING FORMAT MATCH
def format_match(
    target: str | Callable[..., str], kwargs: dict[str, Any], args: tuple[Any, ...]
) -> str:
    """
    Applies named keyword arguments or positional arguments to a string template or callable transformer.

    Args:
        target (str | Callable[..., str]): The string template or callable function to evaluate.
        kwargs (dict[str, Any]): Keyword arguments to pass to the target if provided.
        args (tuple[Any, ...]): Positional arguments to pass to the target if keyword arguments are absent.

    Returns:
        str: The formatted string result.
    """
    # CALLABLE TARGET DISPATCH
    # Evaluates the target as a callable function, passing keyword arguments if present or positional arguments otherwise.
    if callable(target):
        return target(**kwargs) if kwargs else target(*args)

    # STRING TEMPLATE FORMATTING
    # Formats the string template target, injecting keyword arguments if present or positional arguments otherwise.
    else:
        return target.format(**kwargs) if kwargs else target.format(*args)
