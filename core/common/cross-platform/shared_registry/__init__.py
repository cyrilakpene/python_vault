from .registry import GenericRegistry  # type: ignore[import-not-found]
from .singleton import registry  # type: ignore[import-not-found]

__all__ = ["GenericRegistry", "registry"]
