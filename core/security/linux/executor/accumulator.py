import re
import sys
from typing import Any

from .compilation import (
    compile_suppression_patterns,  # type: ignore[import-not-found]
    compile_suppression_ranges,  # type: ignore[import-not-found]
    filter_and_write_line,  # type: ignore[import-not-found]
    process_chunk_data,  # type: ignore[import-not-found]
)


# STREAM TEXT ACCUMULATOR & REGEX SUPPRESSION ENGINE
# Manages line-buffered streaming output across PTY chunk boundaries, detecting sensitive output
# matching configured suppression rules or multi-line block ranges, suppressing matched lines silently
# from live terminal displays, and logging occurrences via report_status() while preserving complete output history in memory.
class TextAccumulator:
    """Buffers live PTY byte chunks into text lines to evaluate sensitive pattern rules
    and multi-line suppression ranges, silently suppressing matching output from sys.stdout while logging events.
    """

    # STREAMING FILTER SUBSYSTEM: SUPPRESSION FILTER INITIALIZATION
    # This initializer sets up the stream suppression filter by compiling regex patterns and ranges
    # for output filtering, and initializing the internal streaming state dictionary
    # to track line buffers, active suppression ranges, and prompt states.
    def __init__(
        self,
        suppress_patterns: list[str | re.Pattern[str]] | None = None,
        suppress_ranges: (
            list[tuple[str | re.Pattern[str], str | re.Pattern[str]]] | None
        ) = None,
    ):
        """
        Initializes the streaming output suppression filter with compilation utilities and state tracking.

        Args:
            suppress_patterns (list[str | re.Pattern[str]] | None, optional): Patterns to match and suppress in the stream. Defaults to None.
            suppress_ranges (list[tuple[str | re.Pattern[str], str | re.Pattern[str]]] | None, optional): Start/end range boundaries for suppression. Defaults to None.
        """
        # PATTERN & RANGE COMPILATION
        # Compile suppression patterns and range boundary definitions using external modular utilities.
        self.compiled_patterns = compile_suppression_patterns(suppress_patterns)
        self.compiled_ranges = compile_suppression_ranges(suppress_ranges)

        # STREAMING STATE INITIALIZATION
        # Initialize the state dictionary for tracking line buffers, active range indices, and prompt indicators.
        self.state: dict[str, Any] = {
            "line_buffer": "",
            "active_range_idx": None,
            "last_was_prompt": False,
        }

    # STREAMING FILTER SUBSYSTEM: RAW BYTE CHUNK PROCESSING
    # This method processes raw incoming byte chunks from the PTY master by delegating
    # to a functional data processor utility, passing compiled patterns, ranges, and internal state.
    def process_bytes(self, chunk: bytes) -> None:
        """
        Processes raw byte chunks from the PTY master by calling the functional chunk processor.

        Args:
            chunk (bytes): Raw byte chunk received from the PTY master stream.
        """
        # PROCESSOR DELEGATION: EXTERNAL PROCESS_CHUNK_DATA INVOCATION
        # Delegate byte decoding, pattern matching, range boundary evaluation, and state updates
        # to the centralized process_chunk_data utility, passing the chunk, compiled patterns, ranges, and state.
        process_chunk_data(
            chunk,
            self.compiled_patterns,
            self.compiled_ranges,
            self.state,
        )

    # STREAMING FILTER SUBSYSTEM: TRAILING BUFFER FLUSHING
    # This method flushes any remaining contents in the line buffer upon child process exit
    # by applying filtering rules, writing the output, clearing the buffer, and flushing standard output.
    def flush(self) -> None:
        """
        Flushes any remaining trailing buffer contents upon child process exit.
        """
        # BUFFER CONTENT EVALUATION
        # Check if any unwritten data remains in the internal line buffer.
        if self.state["line_buffer"]:
            # FILTERING & WRITING DELEGATION
            # Delegate line filtering, pattern matching, and output writing to the external utility.
            filter_and_write_line(
                self.state["line_buffer"],
                self.compiled_patterns,
                self.compiled_ranges,
                self.state,
            )

            # BUFFER CLEARING & STDOUT FLUSH
            # Reset the line buffer and force a flush on standard output to ensure delivery.
            self.state["line_buffer"] = ""
            sys.stdout.flush()
