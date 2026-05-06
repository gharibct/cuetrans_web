# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python FastAPI service that replaces a legacy Java JMSServlet. Part of the CueTrans web platform (enterprise workflow/constraint management). Accepts workflow requests with form-encoded data and routes them to service handlers. Handles workflows like CoreTenantService, CoreAdminService, and CoreConstraintService.

## Commands

```bash
# Install dependencies (use venv)
pip install -r requirements.txt

# Run the server (port 8000)
python main.py
# Or with hot reload:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

No test framework, linter, or formatter is configured yet.

## Architecture

Layered FastAPI application:

- **`main.py`** - App entry point. Loads logging config from `core/logging.yaml`, registers CORS middleware, includes routers.
- **`api/routes/`** - Route handlers (controllers). Each router is registered in the `routes` list in `main.py`.
- **`schemas/`** - Pydantic v2 models for request/response validation. `JMSRequest` accepts `workFlowName`, `workFlowParams` (JSON string), `processType`, `AuthToken`. `JMSResponse` returns `hdrcache` (list of dicts).
- **`services/`** - Business logic. `workflow_handler.py` parses `workFlowParams` from JSON string to dict and dispatches workflows.
- **`core/`** - Configuration (currently logging only via YAML).

## Key Endpoints

- `POST /JMSServlet/` - Main workflow endpoint (mirrors the original Java servlet path)
- `GET /health` - Health check
- `POST /test-jms` - Test endpoint defined directly in `main.py`

## Request/Response Contract

Requests use the original servlet's form-encoded format with `workFlowParams` as a JSON string. Responses return `{"hdrcache": [{"hdnAuthToken": "..."}]}` to match the legacy format consumed by the ExtJS frontend (`Ext.JSON.decode`).

## Development Notes

- The workflow handler (`services/workflow_handler.py`) is currently stubbed with a TODO for actual business logic.
- Logging writes to both console and `app.log` (rotating, 10MB, 5 backups).
- `main.py` must be run from the `jms_listener/` directory because it loads `./core/logging.yaml` via relative path.
- The README.md describes a planned folder structure (models, repositories, events, outbox, consumers) that will be added incrementally.
