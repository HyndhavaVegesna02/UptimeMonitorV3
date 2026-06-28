---
title: API Five-File Feature Convention
code_refs: [backend/src/api/v1/decisions/__init__.py, backend/src/api/v1/decisions/controller.py, backend/src/api/v1/decisions/models.py, backend/src/api/v1/decisions/validation.py, backend/src/api/v1/decisions/service.py, backend/src/composition/app.py, pyproject.toml]
verified_sha: c3a1a11
verified_sprint: sprint-12
status: verified
---

## Facts (verified against code)
- The five-file API convention (dossier §13) divides each endpoint feature directory (e.g. `api/v1/decisions/`) into exactly five modules:
  - `__init__.py`: Router re-export only (`api/v1/decisions/__init__.py`).
  - `controller.py`: Exposes HTTP routes, parameters, and status codes with no business logic (`api/v1/decisions/controller.py::create_decision`).
  - `models.py`: Defines Pydantic DTOs for HTTP input and output, keeping domain models encapsulated (`api/v1/decisions/models.py::DecisionRequest`).
  - `validation.py`: Performs syntactic checks using the Python standard library only, raising structured validation errors (`api/v1/decisions/validation.py::validate_decision_request`).
  - `service.py`: Performs the thin orchestration layer by validating input, resolving core services via dependencies, and shaping the DTO response (`api/v1/decisions/service.py::DecisionService.record_decision`).
- The `api-feature-independence` contract in `pyproject.toml` prevents horizontal features from importing each other.
- The FastAPI application factory in `composition/app.py::create_app` wires adapters, clocks, and services into the application state for dependency injection.
