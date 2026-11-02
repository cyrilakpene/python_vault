import re
from typing import Callable, Iterable, TextIO

from .matcher import intercept_line  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: REAL-TIME STREAM RENDERING & IN-PLACE REWRITING
# This utility consumes line generators in real-time, evaluates lines against patterns,
# and performs in-place stream rewriting with proper carriage returns and flushing.
# [>] EXECUTING STREAM LINE RENDERING
def render_stream_lines(
    line_generator: Iterable[str],
    pattern: re.Pattern[str],
    target: str | Callable[..., str],
    stream: TextIO,
) -> None:
    """
    Consumes line streams in real-time, rewriting pattern-matched progress lines in-place.

    Args:
        line_generator (Iterable[str]): An iterable yielding raw text lines from a stream.
        pattern (re.Pattern[str]): The compiled regular expression pattern to match progress lines.
        target (str | Callable[..., str]): The formatting string template or callable transformer for matched lines.
        stream (TextIO): The output text stream (e.g., sys.stdout or sys.stderr) to write rendered lines.

    Returns:
        None
    """
    # INTERCEPTION STATE INITIALIZATION
    # Tracks whether the previously rendered line was an intercepted and rewritten progress line.
    last_was_intercepted = False

    # STREAM GENERATOR ITERATION & CONSUMPTION
    # Iterates through each incoming line from the generator in real-time.
    for line in line_generator:
        matched = bool(pattern.search(line))
        clean_line = intercept_line(line=line, pattern=pattern, target=target).rstrip(
            "\r\n"
        )

        # MATCHED PROGRESS LINE HANDLING
        # Writes matched lines in-place using carriage returns to facilitate dynamic progress updates.
        if matched:
            stream.write(f"\r{clean_line}")
            stream.flush()
            last_was_intercepted = True

        # STANDARD LINE HANDLING
        # Writes standard unmatched lines, ensuring preceding intercepted progress lines are properly terminated.
        else:
            if last_was_intercepted:
                stream.write("\n")
            stream.write(f"{clean_line}\n")
            stream.flush()
            last_was_intercepted = False

    # FINAL STREAM FLUSH & NEWLINE TERMINATION
    # Appends a final newline if the stream concluded with an active intercepted progress line.
    if last_was_intercepted:
        stream.write("\n")
        stream.flush()
