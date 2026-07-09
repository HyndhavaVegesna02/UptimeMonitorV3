"""Shared syntactic-validation exception type for the API edge.

Cites: Proposal (2026-07-10) §6.2, §6.4.
The `_shared` package owns cross-feature HTTP-edge concerns. Each feature's
`validation.py` raises this ONE exception type for syntactic (pre-domain)
request validation failures, so `_shared/errors.py` can map it to HTTP 422
without `_shared` ever importing a feature package (the forbidden direction
under the `api-shared-no-feature-imports` contract is `_shared` -> feature;
features importing FROM `_shared` is the allowed direction).
"""


class SyntacticValidationError(ValueError):
    """Raised when incoming request data fails syntactic (pre-domain) validation."""
