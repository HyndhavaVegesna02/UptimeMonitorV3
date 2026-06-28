---
title: API Five-File Feature Convention
code_refs: [backend/src/api/v1/decisions/__init__.py, backend/src/api/v1/decisions/controller.py, backend/src/api/v1/decisions/models.py, backend/src/api/v1/decisions/validation.py, backend/src/api/v1/decisions/service.py, backend/src/api/v1/components/__init__.py, backend/src/api/v1/components/controller.py, backend/src/api/v1/components/models.py, backend/src/api/v1/components/validation.py, backend/src/api/v1/components/service.py, backend/src/api/v1/approvals/__init__.py, backend/src/api/v1/approvals/controller.py, backend/src/api/v1/approvals/models.py, backend/src/api/v1/approvals/validation.py, backend/src/api/v1/approvals/service.py, backend/src/composition/app.py, pyproject.toml]
verified_sha: 08c4eba
verified_sprint: sprint-13
status: verified
---

## Facts (verified against code)
- The five-file API convention (dossier §13) divides each endpoint feature directory (e.g. `api/v1/decisions/`, `api/v1/components/`, `api/v1/approvals/`) into exactly five modules:
  - `__init__.py`: Router re-export only (`api/v1/decisions/__init__.py`, `api/v1/components/__init__.py`, `api/v1/approvals/__init__.py`).
  - `controller.py`: Exposes HTTP routes, parameters, and status codes with no business logic (`api/v1/decisions/controller.py::create_decision`, `api/v1/components/controller.py::list_components`, `api/v1/approvals/controller.py::list_open_proposals`).
  - `models.py`: Defines Pydantic DTOs for HTTP input and output, keeping domain models encapsulated (`api/v1/decisions/models.py::DecisionRequest`, `api/v1/components/models.py::ComponentDTO`, `api/v1/approvals/models.py::ProposalDTO`).
  - `validation.py`: Performs syntactic checks using the Python standard library only, raising structured validation errors (`api/v1/decisions/validation.py::validate_decision_request`, `api/v1/components/validation.py`, `api/v1/approvals/validation.py`).
  - `service.py`: Performs the thin orchestration layer by validating input, resolving core services via dependencies, and shaping the DTO response (`api/v1/decisions/service.py::DecisionService.record_decision`, `api/v1/components/service.py::ComponentsService.get_all_components`, `api/v1/approvals/service.py::ApprovalsService.get_open_proposals`).
- The `api-feature-independence` contract in `pyproject.toml` prevents horizontal features from importing each other (currently forbids imports between `src.api.v1.decisions`, `src.api.v1.health`, `src.api.v1.components`, and `src.api.v1.approvals`).
- The feature's FastAPI DI provider (`service.py::get_decision_service`, `service.py::get_components_service`, `service.py::get_approvals_service`) lives in the feature's own `service.py` (which may import the container), so `controller.py` imports ONLY this feature's `models` + `service` — no core type leaks into the controller (AC1).
- The FastAPI application factory in `composition/app.py::create_app` wires adapters, clocks, and services into the application state for dependency injection.

