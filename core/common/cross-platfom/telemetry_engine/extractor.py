import re
from typing import Any, cast

from .inference import infer_type  # type: ignore[import-not-found]
from .models import MetricConfig  # type: ignore[import-not-found]


# TELEMETRY SUBSYSTEM: LOG METRICS EXTRACTION & REGEX PARSING
# This utility scans log text buffers against schema regex patterns to extract
# singular or aggregate telemetry markers with strict key validation, dataclass/dict handling, and type inference.
# [>] EXECUTING LOG METRICS EXTRACTION
def extract_metrics(
    log_text: str,
    metrics_cfg: dict[str, Any],
    return_all: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """
    Scans the log buffer against schema regex patterns to extract telemetry markers.

    Args:
        log_text (str): The raw log text buffer to scan.
        metrics_cfg (dict[str, Any]): Configuration dictionary defining patterns and rules for each metric.
        return_all (bool): Flag indicating whether to extract all occurrences or only the first match.

    Returns:
        tuple[dict[str, Any], list[str]]: A tuple containing the extracted metrics manifest dictionary
        and a list of missing strict metric keys.
    """
    manifest: dict[str, Any] = {}
    missing_strict_keys: list[str] = []

    # METRIC CONFIGURATION ITERATION LOOP
    # Iterates through each configured metric variable to extract data based on its regex and rules.
    for var_name, config in metrics_cfg.items():
        # CONFIGURATION TYPE & DATACLASS RESOLUTION
        # Normalizes configuration parameters depending on whether they are defined as a MetricConfig dataclass, legacy dict, or raw pattern string.
        if isinstance(config, MetricConfig):
            raw_pattern = config.regex
            default = config.default
            is_strict = config.strict
            target_group = config.group
        elif isinstance(config, dict):
            config_dict = cast(dict[str, Any], config)
            raw_pattern = config_dict.get("regex", "")
            default = config_dict.get("default")
            is_strict = config_dict.get("strict", False)
            target_group = config_dict.get("group", 1)
        else:
            raw_pattern = config
            default = None
            is_strict = False
            target_group = 1

        # REGEX PATTERN COMPILATION
        # Compiles or casts the regex pattern object with multi-line, case-insensitive, and dot-all flags.
        if isinstance(raw_pattern, re.Pattern):
            pattern_obj = cast(re.Pattern[str], raw_pattern)
        else:
            pattern_obj = re.compile(
                str(raw_pattern), re.MULTILINE | re.IGNORECASE | re.DOTALL
            )

        # AGGREGATE EXTRACTION BRANCH (RETURN ALL MATCHES)
        # Finds all pattern occurrences in the log text and processes captured groups into a list.
        if return_all:
            matches_list = pattern_obj.findall(log_text)
            if matches_list:
                idx = target_group - 1 if isinstance(target_group, int) else 0
                manifest[var_name] = [
                    infer_type(m[idx] if isinstance(m, tuple) else m)
                    for m in matches_list
                ]
            else:
                manifest[var_name] = default or []
                if is_strict:
                    missing_strict_keys.append(var_name)

        # SINGULAR EXTRACTION BRANCH (FIRST MATCH ONLY)
        # Searches for the first pattern occurrence and extracts the specified target group.
        else:
            match_obj = pattern_obj.search(log_text)
            if match_obj:
                try:
                    if isinstance(target_group, (tuple, list)):
                        groups = cast(
                            tuple[int | str, ...] | list[int | str], target_group
                        )
                        captured_list = [match_obj.group(g) for g in groups]
                        manifest[var_name] = [infer_type(c) for c in captured_list]
                    else:
                        captured = match_obj.group(target_group)
                        manifest[var_name] = infer_type(captured)
                except (IndexError, KeyError):
                    captured = (
                        match_obj.group(1)
                        if match_obj.lastindex
                        else match_obj.group(0)
                    )
                    manifest[var_name] = infer_type(captured)
            else:
                manifest[var_name] = default
                if is_strict:
                    missing_strict_keys.append(var_name)

    # METRICS MANIFEST RETURN
    # Returns the completed metrics dictionary along with any missing strict keys.
    return manifest, missing_strict_keys
