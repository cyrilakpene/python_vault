# SYSTEM UTILITIES SUBSYSTEM: DYNAMIC END POINT CALCULATION
# This utility calculates the dynamic end boundary for processing chunks by adding an interval
# to a starting point and clamping the result against the total maximum runtime limit.
# [>] EXECUTING DYNAMIC END CALCULATION
def calculate_dynamic_end(start_point: int, runtime: int, interval: int = 60) -> int:
    """
    Calculates the dynamic end boundary for processing chunks by adding an interval,
    clamped against the total runtime limit.

    Args:
        start_point (int): The starting point or offset for the current chunk.
        runtime (int): The maximum total runtime limit.
        interval (int): The step interval size to advance (defaults to 60).

    Returns:
        int: The calculated end point, safely capped at the total runtime limit.
    """
    # BOUNDARY CAPPING & CALCULATION
    # Computes the target end position by adding the interval to the start point,
    # ensuring it does not exceed the maximum allowable runtime boundary.
    return min(runtime, start_point + interval)


# SYSTEM UTILITIES SUBSYSTEM: MIDPOINT START POINT CALCULATION
# This utility calculates the heuristic start point for preview windows by finding the midpoint
# of the total runtime and applying a fixed backward offset, clamped at zero.
# [>] EXECUTING MIDPOINT START CALCULATION
def calculate_midpoint_start(runtime_seconds: int) -> int:
    """
    Calculates the mid-point heuristic start point for preview windows.

    Args:
        runtime_seconds (int): The total media runtime duration in seconds.

    Returns:
        int: The calculated start point in seconds, floored at zero.
    """
    # MIDPOINT CALCULATION
    # Determines the exact center point of the total runtime duration.
    mid_point: int = int(runtime_seconds / 2)

    # BACKWARD OFFSET & FLOOR CLAMPING
    # Applies a 30-second backward offset for preview context and clamps the result at zero.
    return max(0, mid_point - 30)
