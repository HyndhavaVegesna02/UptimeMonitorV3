"""composition — the wiring / "main" layer; the only zone importing both sides."""

from src.composition.publish_helper import publish_best_effort

__all__ = [
    "publish_best_effort",
]
