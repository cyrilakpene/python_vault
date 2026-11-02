# SYSTEM UTILITIES SUBSYSTEM: TIME DURATION FORMATTING
# This utility converts an integer count of seconds into a standardized,
# zero-padded 'HH:MM:SS' time duration string.
# [>] EXECUTING TIME DURATION FORMATTING
def format_seconds(seconds: int) -> str:
    """
    Converts an integer count of seconds into a standardized,
    zero-padded 'HH:MM:SS' time duration string.

    Args:
        seconds (int): The total duration in seconds to format.

    Returns:
        str: The formatted time string in 'HH:MM:SS' format.
    """
    # TIME CONVERSION: HOUR CALCULATION
    # Extracts total full hours from the given seconds count.
    hours: int = seconds // 3600

    # TIME CONVERSION: MINUTE CALCULATION
    # Extracts remaining minutes from the seconds count after removing hours.
    minutes: int = (seconds % 3600) // 60

    # TIME CONVERSION: SECOND CALCULATION
    # Extracts remaining seconds after removing full hours and minutes.
    secs: int = seconds % 60

    # ZERO-PADDED STRING FORMATTING
    # Formats the time components into a standard zero-padded colon-delimited string.
    return f"{hours:02}:{minutes:02}:{secs:02}"
