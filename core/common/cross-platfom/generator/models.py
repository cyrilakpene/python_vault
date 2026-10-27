from dataclasses import dataclass, asdict
from typing import Any


# DATA JOB SUBSYSTEM: BASE METADATA DATACLASS
# This utility provides a type-safe base dataclass with automatic dictionary conversion
# capabilities for job identification and metadata sanitization.
# [>] EXECUTING BASE JOB DATA DATACLASS DEFINITION
@dataclass
class BaseJobData:
    """
    Base dataclass providing type-safe metadata definition
    and automatic dictionary conversion for job ID generation.
    """

    # DICTIONARY CONVERSION METHOD
    # Converts the dataclass fields into a standard dictionary format for sanitization.
    def to_dict(self) -> dict[str, Any]:
        """Converts the dataclass fields into a dictionary for sanitization."""
        return asdict(self)
