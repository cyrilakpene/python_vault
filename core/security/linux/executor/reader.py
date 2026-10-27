import queue


# SYSTEM UTILITIES SUBSYSTEM: NON-BLOCKING OUTPUT QUEUE READER
# This utility retrieves the next line of output from a synchronized queue in a non-blocking manner,
# returning None if the queue is empty or uninitialized.
# [>] EXECUTING NON-BLOCKING QUEUE READ
def read_line(out_queue: queue.Queue[str] | None) -> str | None:
    """
    Retrieves the next line of output if available, else returns None.

    Args:
        out_queue (queue.Queue[str] | None): The thread-safe queue containing buffered output strings, or None.

    Returns:
        str | None: The next available string line from the queue, or None if empty or uninitialized.
    """
    # QUEUE AVAILABILITY & NON-BLOCKING RETRIEVAL
    # Checks if the output queue exists, then attempts an immediate non-blocking retrieval,
    # gracefully capturing queue empty exceptions.
    if out_queue is None:
        return None

    try:
        return out_queue.get_nowait()
    except queue.Empty:
        return None


# SYSTEM UTILITIES SUBSYSTEM: BATCHED OUTPUT QUEUE DRAIN
# This utility drains all available lines from an output queue in a non-blocking loop,
# respecting the exhaustion state and returning accumulated string lines.
# [>] EXECUTING BATCHED QUEUE DRAIN
def read_all(is_exhausted: bool, out_queue: queue.Queue[str] | None) -> list[str]:
    """
    Drains and returns all available output lines from the queue until exhausted or empty.

    Args:
        is_exhausted (bool): Flag indicating whether the stream output is already exhausted.
        out_queue (queue.Queue[str] | None): The thread-safe queue containing buffered output strings, or None.

    Returns:
        list[str]: A list of accumulated output lines drained from the queue.
    """
    # COLLECTION INITIALIZATION & EXHAUSTION GUARD
    # Initializes the lines collection and returns immediately if the stream is already marked as exhausted.
    lines: list[str] = []
    if is_exhausted:
        return lines

    # QUEUE DRAINING LOOP
    # Continuously reads lines from the queue using non-blocking retrieval until the queue is empty
    # or signals end-of-stream (None).
    while True:
        try:
            line: str | None = read_line(out_queue)
            if line is None:
                is_exhausted = True
                break
            lines.append(line)
        except queue.Empty:
            break

    return lines
