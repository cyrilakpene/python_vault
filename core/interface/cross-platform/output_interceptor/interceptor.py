import re
import sys
from typing import Callable, Iterable, TextIO

from .matcher import intercept_line  # type: ignore[import-not-found]
from .renderer import render_stream_lines  # type: ignore[import-not-found]


# SYSTEM INTERCEPT STRATEGY & STREAM DIRECTION CONTROLLER
# CONCRETE CAPTURE WRAPPER: I/O BUFFERS & TERMINAL REDIRECTION ENGINE
# Intercepts standard output streams to capture, filter, and reroute system-level console emissions.
# By wrapping file descriptors and stdout/stderr handles, it enables real-time telemetry streaming
# and live diagnostic captures without disrupting core execution threads.
class OutputInterceptor:
    """Intercepts standard output streams to capture, filter, and reroute system-level console emissions.

    Provides non-blocking stream capture and buffer management, ensuring that standard console
    outputs can be monitored, filtered, and redirected securely during active runtime operations.
    """

    # STREAM FILTERING SUBSYSTEM: FILTER INITIALIZATION
    # This initializer sets up the stream suppression filter by compiling the target regex pattern,
    # establishing the formatting template or replacement callable, and configuring the output text stream.
    def __init__(
        self,
        pattern: str,
        template: str | Callable[..., str],
        stream: TextIO = sys.stdout,
    ):
        """
        Initializes the stream suppression filter with a regular expression pattern,
        a replacement template or callable, and an output stream destination.

        Args:
            pattern (str): The regular expression pattern used to match target lines or strings in the stream.
            template (str | Callable[..., str]): The replacement template string or callable function
                used to format filtered output.
            stream (TextIO, optional): The target output text stream destination. Defaults to sys.stdout.
        """
        # REGEX PATTERN COMPILATION
        # Compile the provided string pattern into an efficient regular expression object for matching.
        self.pattern = re.compile(pattern)

        # TARGET TEMPLATE ASSIGNMENT
        # Store the target template string or callable formatter for transforming matched output.
        self.target = template

        # OUTPUT STREAM CONFIGURATION
        # Bind the target output text stream for filtered data dispatch.
        self.stream = stream

    # STREAM FILTERING SUBSYSTEM: LINE INTERCEPTION & TRANSFORMATION
    # This method intercepts incoming text lines, matching against compiled regular expression patterns
    # and delegating transformation to an external matcher utility.
    def intercept(self, line: str) -> str:
        """
        Intercepts an incoming line of text, delegating line interception and transformation
        to the external matcher utility using the compiled pattern and target template.

        Args:
            line (str): The incoming line of text to be evaluated and potentially transformed.

        Returns:
            str: The resulting intercepted or transformed line of text.
        """
        # LINE INTERCEPTION & TRANSFORMATION DELEGATION
        # Delegate line matching, filtering, and template transformation to the centralized
        # intercept_line utility, passing the line, compiled regex pattern, and target template.
        return intercept_line(
            line=line,
            pattern=self.pattern,
            target=self.target,
        )

    # STREAM FILTERING SUBSYSTEM: STREAM RENDERING
    # This method orchestrates the stream rendering process over an iterable line generator,
    # delegating buffering, filtering, transformation, and output writing to an external renderer utility.
    def render_stream(self, line_generator: Iterable[str]) -> None:
        """
        Orchestrates stream rendering over an iterable line generator, delegating stream rendering
        and buffer loop execution to the external renderer utility.

        Args:
            line_generator (Iterable[str]): An iterable collection of text lines to be processed,
                filtered, and rendered to the target output stream.
        """
        # STREAM RENDERING DELEGATION
        # Delegate stream processing, pattern matching, template substitution, and direct
        # stream writing to the centralized render_stream_lines utility.
        render_stream_lines(
            line_generator=line_generator,
            pattern=self.pattern,
            target=self.target,
            stream=self.stream,
        )
