"""Syntactic checks for decisions (api/v1/decisions zone).

Uses stdlib only (no service/core imports). Cites dossier §13.
"""


class SyntacticValidationError(ValueError):
    """Raised when incoming decision request fails syntactic validation."""


def validate_decision_request(action: str, actor: str) -> None:
    """Perform syntactic validation on the decision request parameters."""
    if action not in ("approve", "reject"):
        raise SyntacticValidationError(
            f"Action must be 'approve' or 'reject', got {action!r}."
        )

    if not actor.strip():
        raise SyntacticValidationError("Actor must be a non-empty string.")
