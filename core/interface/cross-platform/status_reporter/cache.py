# PERSISTENCE LAYER: LOOP STATE CACHE
# This dictionary tracks the last-rendered timestamp for specific messages.
# By residing at the module level, it persists across multiple function calls
# within the same execution session, enabling time-based filtering.
LOOP_CACHE: dict[str, float | int] = {}
