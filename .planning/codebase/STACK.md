# Technology Stack

**Analysis Date:** 2026-03-11

## Languages

**Backend:**
- Python 3.12+ - FastAPI async backend, business logic, workers

**Frontend:**
- TypeScript ~5.9.3 - React client with strict type checking
- HTML/CSS - JSX templates and Tailwind CSS styling

## Runtime

**Environment:**
- Python 3.12 (backend)
- Node.js (frontend, via Vite)

**Package Manager:**
- `uv` (Python, backend) - dependency management and task runner
- `npm` (Node.js, frontend) - package management
- Lockfile: `uv.lock` (present), `package-lock.json` (present)

## Frameworks

**Backend - Core:**
- FastAPI 0.115.0+ - REST API framework, async HTTP server
- SQLAlchemy 2.x with asyncio - async ORM for database modeling and queries

**Backend - Infrastructure:**
- Uvicorn 0.34.0+ - ASGI server
- Alembic 1.14.0+ - Database schema migrations
- Dramatiq 1.17.0 with Redis - Distributed task queue for post publishing
- APScheduler 3.10.0+ - Background job scheduler for polling scheduled posts

**Frontend - Core:**
- React 19.2.0 - UI framework
- React Router 7.13.1 - Client-side routing
- Vite 7.3.1 - Build tool and dev server

**Frontend - Styling:**
- Tailwind CSS 4.2.1 - Utility-first CSS framework
- Tailwind CSS Vite plugin 4.2.1 - Vite integration

**Frontend - Development:**
- TypeScript 5.9.3 - Type checking
- ESLint 9.39.1 - Linting
- Vite React plugin 5.1.1 - React integration for Vite

## Key Dependencies

**Backend - Database:**
- asyncpg 0.30.0+ - PostgreSQL async driver

**Backend - Authentication:**
- python-jose 3.3.0+ with cryptography - JWT token creation and validation
- bcrypt 4.0.0+ - Password hashing

**Backend - HTTP & Integration:**
- httpx 0.28.0+ - Async HTTP client for external API calls (Facebook, Instagram)

**Backend - Data Validation:**
- Pydantic 2.0+ - Request/response schema validation
- Pydantic Settings 2.0+ - Configuration management

**Backend - Utilities:**
- python-multipart 0.0.18+ - Form data parsing for OAuth callbacks

**Backend - Testing:**
- pytest 8.0.0+ - Test runner
- pytest-asyncio 0.24.0+ - Async test support
- pytest-factoryboy 2.7.0+ - Test fixtures via factories
- pytest-cov 6.0.0+ - Coverage reporting
- faker 33.0.0+ - Fake data generation
- aiosqlite 0.20.0+ - SQLite support for testing

**Backend - Linting:**
- ruff 0.8.0+ - Python linter and formatter

## Configuration

**Backend Environment:**
- Configuration via `pydantic-settings` with `.env` file support
- Critical env vars: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`
- Database URLs: separate dev (port 5434) and test (port 5433) PostgreSQL instances
- Redis: localhost:6379 for task queue

**Frontend Environment:**
- Configuration via environment variables injected by Vite
- API base URL: `/api/v1` with dev proxy to `http://localhost:8000`
- Vite proxy config in `vite.config.ts` handles dev-time backend proxying

**Build:**
- Backend: Hatchling build system configured in `pyproject.toml`
- Frontend: Vite config in `src/client/vite.config.ts` with @ path alias to `src/`

## Database

**Primary:** PostgreSQL 17 (via Docker)
- Connection: SQLAlchemy async with asyncpg driver
- Schema: Managed by Alembic migrations in `alembic/` directory
- Multi-user isolation: Queries scoped by `current_user.id`

**Test Database:** Separate PostgreSQL 17 instance (port 5433)
- Recreated fresh for each test function via `setup_database` fixture
- Used for integration tests and e2e test scenarios

## Caching & Task Queue

**Task Broker:** Redis 7-alpine
- Dramatiq Redis broker for async task publishing
- APScheduler integration for background job scheduling
- Task retry policy: max 3 retries with exponential backoff (1-60s)

## Docker

**Image:** Multi-stage or unified Dockerfile for application
- Includes uvicorn for API server
- Includes dramatiq worker runtime
- Environment configuration via `.env` file mounted at runtime

**Compose Services:**
- `db`: PostgreSQL 17 primary instance (port 5434)
- `db-test`: PostgreSQL 17 test instance (port 5433)
- `redis`: Redis 7 message broker (port 6379)
- `api`: FastAPI application (port 8000)
- `worker`: Dramatiq worker process for task execution

---

*Stack analysis: 2026-03-11*
