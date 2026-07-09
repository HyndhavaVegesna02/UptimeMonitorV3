"""Syntactic checks for decisions (api/v1/decisions zone).

No service/core imports. Cites dossier §13. `SyntacticValidationError` is
re-exported here for back-compat (STORY-075, Proposal (2026-07-10) §6.2/§6.4)
— it is now defined once in `_shared/validation.py` so `_shared/errors.py` can
map it to HTTP 422 without importing this feature package.
"""

from src.api.v1._shared.validation import SyntacticValidationError

__all__ = ["SyntacticValidationError", "validate_decision_request"]


def validate_decision_request(action: str, actor: str) -> None:
    """Perform syntactic validation on the decision request parameters."""
    if action not in ("approve", "reject"):
        raise SyntacticValidationError(
            f"Action must be 'approve' or 'reject', got {action!r}."
        )

    if not actor.strip():
        raise SyntacticValidationError("Actor must be a non-empty string.")
