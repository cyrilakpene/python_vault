from typing import Any


# ARCHITECTURAL GATEKEEPER: VARIABLE-STRICTNESS DEEP IDENTITY RESOLUTION ENGINE
# This engine serves as the "Identity Auditor." It facilitates high-precision
# lookups across complex metadata repositories (e.g., your Anime/Donghua
# encoding database). By supporting both O(1) Label lookups and Deep-Path
# Traversal, it ensures that records can be retrieved even when only
# partial "Fingerprints" (like a Release Group or Codec) are available.
def find_match_in_identity(
    identity_map: dict[str, Any] | None, strict: bool = True, **search_criteria: Any
) -> dict[str, Any] | None:
    """
    Scans a keyed dictionary to locate records by Label or nested Content.
    Supports recursive traversal and configurable parity enforcement (ALL vs ANY).
    """

    # PRE-FLIGHT IDENTITY VALIDATION: NULL-SAFETY GATE
    # If the provided 'identity_map' is 'None' or empty, we return 'None'
    # immediately. This prevents 'TypeError' during traversal and satisfies
    # static type checkers (Pylance/MyPy) in hardened environments.
    # [!] VALIDATING IDENTITY REPOSITORY
    if not identity_map:
        return None

    def resolve_nested_attribute(data: Any, target_key: str) -> Any:
        """
        RECURSIVE ATTRIBUTE RESOLVER: DEPTH-FIRST SEARCH (DFS)
        Performs a recursive audit to locate a key-value pair within
        nested structures (e.g., 'technical.codec' or 'archive.location').
        """
        if isinstance(data, dict):
            if target_key in data:
                return data[target_key]
            for value in data.values():
                result: Any = resolve_nested_attribute(value, target_key)
                if result is not None:
                    return result
        return None

    # PRIMARY LABEL RESOLUTION: O(1) KEY LOOKUP
    # We prioritize a direct dictionary lookup if a 'label' (e.g., 'oshi_no_ko_s02')
    # is provided. This is the most efficient path for known-identity retrieval.
    # [d] PROBING PRIMARY LABEL: {search_criteria.get('label')}
    label_query: Any = search_criteria.get("label")
    if label_query and label_query in identity_map:
        # [+] LABEL RESOLVED: {label_query}
        return identity_map[label_query]

    # CRITERIA ISOLATION: METADATA EXTRACTION
    # We isolate all criteria excluding the 'label'. If no other search
    # parameters remain, we terminate to prevent false-positive matches
    # during the high-overhead deep traversal phase.
    remaining_criteria: dict[str, Any] = {
        k: v for k, v in search_criteria.items() if k != "label"
    }
    if not remaining_criteria:
        return None

    # DEEP CONTENT TRAVERSAL: DYNAMIC IDENTITY SCAN
    # If the label remains unresolved, we iterate through every historical
    # record. This phase audits the internal "Fingerprints" of each entry
    # to verify identity parity.
    # [>] INITIALIZING DEEP SCAN FOR {len(remaining_criteria)} CRITERIA
    for label, content in identity_map.items():

        # DYNAMIC LOGIC SELECTION: PARITY ENFORCEMENT
        # We toggle between 'all()' for strict production environments
        # (requiring a perfect match on all criteria) and 'any()' for
        # loose discovery/fuzzy-search workflows.
        match_logic = all if strict else any

        # ATOMIC CRITERIA VERIFICATION: DEEP PARITY AUDIT
        # We utilize 'resolve_nested_attribute' to ensure that criteria
        # are validated even if they are encapsulated within nested
        # sub-dictionaries (e.g., release_group, vmaf_target).
        is_match: bool = match_logic(
            resolve_nested_attribute(content, key) == value
            for key, value in remaining_criteria.items()
        )

        # MATCH PROMOTION: IDENTITY CONFIRMED
        if is_match:
            # [+] IDENTITY FINGERPRINT MATCHED: {label}
            return content

    # NEGATIVE IDENTITY RESOLUTION: REPROVISIONING SIGNAL
    # [!] NO MATCH FOUND: SIGNALING NEW IDENTITY RECORD REQUIREMENT
    return None
