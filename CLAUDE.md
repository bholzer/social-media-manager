# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Dependencies
uv sync --dev

# Infrastructure (Postgres on 5434, test Postgres on 5433, Redis on 6379)
docker compose up db db-test redis -d

# Run API
uv run uvicorn smm.main:app --reload

# Run Dramatiq worker (separate process)
uv run dramatiq smm.workers.tasks

# Run React client
cd src/client && npm run dev

# Tests
uv run pytest                              # all tests
uv run pytest tests/unit/                  # unit only
uv run pytest tests/integration/           # integration only
uv run pytest tests/unit/test_models.py::TestUserModel::test_create_user  # single test
uv run pytest --cov=smm                    # with coverage

# Lint & format
uv run ruff check src/ tests/             # lint
uv run ruff check --fix src/ tests/       # auto-fix
uv run ruff format src/ tests/            # format

# Migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Architecture

Async Python backend: FastAPI + SQLAlchemy 2.x async + PostgreSQL + Dramatiq (Redis) + APScheduler.

### Layered design

API routes (`api/v1/`) → Services (`services/`) → Models (`models/`). Routes handle HTTP concerns, services contain business logic, models define the schema. Pydantic schemas (`schemas/`) validate request/response payloads separately from ORM models.

### Post publishing pipeline

Posts have multiple PostTargets (one per social account). Each target tracks its own status independently:

```
DRAFT → SCHEDULED → PUBLISHING → PUBLISHED
                               → FAILED
```

Two-layer async processing:
1. **APScheduler** (in FastAPI lifespan): polls DB every 30s, finds targets where `status=scheduled AND post.scheduled_at <= now()`, atomically transitions to `publishing`, enqueues Dramatiq tasks
2. **Dramatiq worker** (separate process): picks up tasks from Redis, resolves the platform adapter via `AdapterRegistry`, calls `adapter.publish()`, updates target to `published` or `failed`

Double-publish prevention: status set to `publishing` before enqueue; worker re-checks status before calling adapter.

### Platform adapter pattern

`AbstractPlatformAdapter` (ABC) defines `publish()` and `validate_token()`. Concrete adapters (Facebook, Instagram) implement platform-specific API calls. `AdapterRegistry` maps `Platform` enum → adapter instance. Add new platforms by creating an adapter class and registering it.

### Authentication

JWT (HS256) for API auth. `get_current_user` dependency extracts and validates Bearer tokens. Facebook OAuth flow uses a separate set of endpoints (`/api/v1/oauth/facebook/*`) that exchange codes for long-lived tokens and store page access tokens.

### Account connection flow

The Facebook OAuth connect flow spans backend and frontend:

1. Frontend calls `GET /api/v1/oauth/facebook/connect` (with Bearer token via `api.get()`), receives `{"url": "..."}` JSON
2. Frontend navigates to the Facebook OAuth URL via `window.location.href`
3. Facebook redirects back to `GET /api/v1/oauth/facebook/callback` on the backend
4. Backend exchanges code for tokens, then redirects to frontend:
   - With pages: `302` to `/accounts/facebook/callback?pages=<encoded>&token=<token>`
   - Profile only: `302` to `/accounts?connected=true`
   - Error: `302` to `/accounts?error=<message>`
5. `FacebookOAuthCallbackPage` handles page selection, calls `POST /api/v1/oauth/facebook/connect-page`
6. User lands on `/accounts` with success banner and refreshed account list

Key detail: `/facebook/connect` returns JSON (not a redirect) because browser navigation can't send the Authorization header.

### Test infrastructure

Tests use a separate Postgres instance (port 5433). The `setup_database` fixture drops and recreates all tables for every test function. The `client` fixture overrides `get_session` to inject the test session. The `authenticated_client` fixture registers a user and sets the Bearer token header. External API calls (Facebook, Dramatiq) are mocked in tests.

All async tests run automatically via `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` decorator needed.

### Key conventions

- All model IDs are UUIDs with `gen_random_uuid()` server default
- All queries scope to `current_user.id` for multi-user isolation
- Services raise `ValueError` for business rule violations; routes convert to 400s
- `StrEnum` for Platform and PostTargetStatus (not `str, Enum`)
- Config via `pydantic-settings` with `.env` file support
