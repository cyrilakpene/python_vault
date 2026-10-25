from typing import TypedDict, NotRequired


# DATA CONTAINER SUBSYSTEM: FILTER FEATURES TYPE DEFINITION
# This TypedDict defines the optional feature flags and configuration toggles
# governing data distillation, strictness, global merging, and atomic flattening behavior.
# [>] DEFINING FILTER FEATURES TYPEDDICT CONFIGURATION
class FilterFeatures(TypedDict):
    """
    Configuration dictionary schema for optional feature flags controlling data filtration and distillation.

    Attributes:
        global_merge (NotRequired[bool]): Flag enabling global consolidation of target keys across nested sub-nodes.
        strict (NotRequired[bool]): Flag enabling strict error handling and path/null validation checks.
        flatten_atomic (NotRequired[bool]): Flag controlling whether single-item atomic branches should be flattened.
    """

    global_merge: NotRequired[bool]
    strict: NotRequired[bool]
    flatten_atomic: NotRequired[bool]
