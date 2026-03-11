# Codebase Structure

**Analysis Date:** 2026-03-11

## Directory Layout

```
social-media-manager/
├── src/
│   ├── smm/                    # Python backend package (namespace: `smm`)
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app creation and router registration
│   │   ├── config.py           # Pydantic Settings for environment configuration
│   │   ├── database.py         # SQLAlchemy async engine and session factory
│   │   ├── dependencies.py     # FastAPI dependency injection (get_session, get_current_user)
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py             # Register, login endpoints
│   │   │   │   ├── users.py            # User profile endpoints
│   │   │   │   ├── posts.py            # Create, read, update, delete, publish-now posts
│   │   │   │   ├── social_accounts.py  # CRUD social accounts
│   │   │   │   └── oauth.py            # Facebook OAuth flow endpoints
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # SQLAlchemy DeclarativeBase with UUID primary key
│   │   │   ├── user.py         # User ORM model
│   │   │   ├── post.py         # Post ORM model
│   │   │   ├── post_target.py  # PostTarget ORM model and PostTargetStatus enum
│   │   │   └── social_account.py # SocialAccount ORM model and Platform enum
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # LoginRequest, RegisterRequest, TokenResponse
│   │   │   ├── user.py         # UserResponse schemas
│   │   │   ├── post.py         # PostCreate, PostUpdate, PostResponse, PostListResponse
│   │   │   └── social_account.py # SocialAccountCreate, SocialAccountResponse
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # register_user, authenticate_user, create_access_token, decode_access_token
│   │   │   ├── post.py         # PostService: create, get, list, update, delete
│   │   │   ├── publisher.py    # publish_target: orchestrates adapter calls
│   │   │   └── facebook_oauth.py # Facebook OAuth token exchange
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # AbstractPlatformAdapter ABC
│   │   │   ├── facebook.py     # FacebookAdapter implementation
│   │   │   ├── instagram.py    # InstagramAdapter implementation
│   │   │   └── registry.py     # AdapterRegistry: maps Platform → Adapter
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── broker.py       # Dramatiq Redis broker configuration
│   │   │   └── tasks.py        # publish_target_task: Dramatiq actor
│   │   └── scheduler/
│   │       ├── __init__.py
│   │       └── scheduler.py    # APScheduler job: poll_and_enqueue
│   │
│   └── client/                 # React + TypeScript + Vite frontend
│       ├── src/
│       │   ├── main.tsx        # React app entry point
│       │   ├── App.tsx         # Root component (RouterProvider)
│       │   ├── router.tsx      # React Router v7 config (ProtectedRoute, GuestRoute)
│       │   ├── layouts/
│       │   │   └── AppLayout.tsx    # Main app layout with nav (Outlet for children)
│       │   ├── pages/
│       │   │   ├── LoginPage.tsx
│       │   │   ├── RegisterPage.tsx
│       │   │   ├── DashboardPage.tsx
│       │   │   ├── PostsPage.tsx
│       │   │   └── AccountsPage.tsx
│       │   └── lib/
│       │       ├── api.ts      # Typed fetch wrapper (api.get, api.post, api.delete)
│       │       └── auth.ts     # isAuthenticated(), localStorage token management
│       ├── public/
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── package.json
│       └── tailwind.config.js  # Tailwind CSS configuration
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # pytest fixtures: test_engine, session, client, authenticated_client
│   ├── factories.py           # factory_boy factories: UserFactory, PostFactory, SocialAccountFactory
│   ├── unit/                  # Unit tests (fast, minimal dependencies)
│   ├── integration/           # Integration tests (full async stack, database)
│   └── e2e/                   # End-to-end tests (full client + API)
│
├── alembic/                   # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── .env                       # Environment configuration (not committed; use .env.example)
├── pyproject.toml            # Python project config, dependencies, pytest settings
├── Dockerfile                # Docker image for backend
├── docker-compose.yml        # Postgres (5434), test Postgres (5433), Redis (6379)
│
└── CLAUDE.md                 # This file: commands, architecture guide for Claude
```

## Directory Purposes

**`src/smm/`:**
- Purpose: Main Python backend package
- Contains: All business logic, database models, API routes, external integrations
- Key files: `main.py` (app entry), `database.py` (session factory), `config.py` (settings)

**`src/smm/api/v1/`:**
- Purpose: HTTP route handlers organized by resource
- Contains: Router instances per resource, endpoint decorators, HTTP error conversion
- Key files: `auth.py`, `posts.py`, `social_accounts.py`, `oauth.py`
- Pattern: Each file is a module-level router; no class-based views

**`src/smm/models/`:**
- Purpose: SQLAlchemy ORM schema definitions
- Contains: Declarative base class, entity classes (User, Post, PostTarget, SocialAccount)
- Key files: `base.py` (Base class with UUID), model classes
- Pattern: 2.x style with Mapped type hints; relationships use back_populates; cascade delete configured

**`src/smm/schemas/`:**
- Purpose: Pydantic request/response validation
- Contains: Request models (PostCreate, LoginRequest), response models (PostResponse, TokenResponse)
- Key files: One file per resource type
- Pattern: Separate from ORM models; nested schemas for complex responses (PostResponse includes targets)

**`src/smm/services/`:**
- Purpose: Business logic, transaction management, validation
- Contains: PostService, AuthService, PublisherService, FacebookOAuthService
- Key files: `post.py` (CRUD and state transitions), `publisher.py` (platform adapter orchestration)
- Pattern: Stateful service classes accepting AsyncSession; methods are async; raise ValueError for violations

**`src/smm/adapters/`:**
- Purpose: Platform-specific social media API implementations
- Contains: Abstract base, concrete adapters (Facebook, Instagram), registry
- Key files: `base.py` (ABC), `registry.py` (Platform → Adapter mapping)
- Pattern: Strategy pattern; new platforms added by subclassing and registering

**`src/smm/workers/`:**
- Purpose: Async background task processing via Dramatiq + Redis
- Contains: Task actors, broker configuration
- Key files: `tasks.py` (publish_target_task Dramatiq actor), `broker.py` (Redis config)
- Pattern: Dramatiq wraps async code via asyncio.run(); tasks are idempotent (re-check status)

**`src/smm/scheduler/`:**
- Purpose: Scheduled post polling and task enqueueing
- Contains: APScheduler job definition, start/stop lifecycle
- Key files: `scheduler.py` (poll_and_enqueue job, BackgroundScheduler)
- Pattern: Runs in FastAPI lifespan; polls every 30s; uses async context to query DB

**`src/client/src/`:**
- Purpose: React client-side application
- Contains: Components (pages, layouts), routing, API client
- Key files: `router.tsx` (routes and guards), `lib/api.ts` (fetch wrapper), `lib/auth.ts` (token management)
- Pattern: Function components; React Router v7; no state management library (local state only)

**`tests/`:**
- Purpose: Automated testing (unit, integration, e2e)
- Contains: Fixtures, factories, test modules
- Key files: `conftest.py` (shared fixtures), `factories.py` (test data generation)
- Pattern: pytest with asyncio_mode=auto; fixtures override get_session to use test DB; external APIs mocked

**`alembic/`:**
- Purpose: Database schema versioning and migrations
- Contains: Migration scripts generated by `alembic revision --autogenerate`
- Pattern: Run with `uv run alembic upgrade head` to apply migrations

## Key File Locations

**Entry Points:**
- `src/smm/main.py`: FastAPI app creation; lifespan context starts scheduler
- `src/smm/workers/tasks.py`: Dramatiq worker entry (separate process)
- `src/client/src/main.tsx`: React app entry; mounts to DOM

**Configuration:**
- `src/smm/config.py`: Pydantic Settings; loads from .env file
- `src/client/src/lib/api.ts`: API_BASE constant and request helper
- `src/client/vite.config.ts`: Vite build config with React plugin

**Core Logic:**
- `src/smm/services/post.py`: PostService handles post CRUD, status transitions, validation
- `src/smm/services/publisher.py`: publish_target orchestrates adapter calls
- `src/smm/adapters/registry.py`: AdapterRegistry maps platforms to adapters

**Testing:**
- `tests/conftest.py`: pytest fixtures (test_engine, session, client, authenticated_client)
- `tests/factories.py`: factory_boy factories for generating test data
- `tests/unit/`, `tests/integration/`: Test modules organized by type

## Naming Conventions

**Files:**
- Python: snake_case (e.g., `post_target.py`, `social_accounts.py`)
- TypeScript: PascalCase for components (e.g., `LoginPage.tsx`), camelCase for utilities (e.g., `api.ts`)
- Test files: `test_*.py` or `*_test.py` (pytest discovery pattern)

**Directories:**
- Python: plural or descriptive nouns (e.g., `models/`, `services/`, `adapters/`, `schemas/`)
- React: feature-based (e.g., `pages/`, `layouts/`, `lib/`)

**Functions:**
- Python: snake_case (e.g., `create_post`, `publish_target`, `authenticate_user`)
- TypeScript: camelCase (e.g., `isAuthenticated`, `api.post()`)

**Classes:**
- Python: PascalCase (e.g., `PostService`, `AbstractPlatformAdapter`, `PostTargetStatus`)
- TypeScript: PascalCase (e.g., `ApiError`)

**Types/Enums:**
- Python: StrEnum for serialization (e.g., `PostTargetStatus`, `Platform`)
- TypeScript: Not heavily typed (limited types in api.ts generics)

**Variables:**
- Python: snake_case (e.g., `target_id`, `access_token`, `published_at`)
- TypeScript: camelCase (e.g., `targetId`, `accessToken`, `publishedAt`)

## Where to Add New Code

**New Feature (e.g., add comment support):**
1. Database models: Add `Comment` class to `src/smm/models/comment.py`
2. Pydantic schemas: Add `CommentCreate`, `CommentResponse` to `src/smm/schemas/comment.py`
3. Service: Add `CommentService` to `src/smm/services/comment.py` with create/list/delete logic
4. API routes: Add `src/smm/api/v1/comments.py` with router and endpoints
5. Register router: Add to `src/smm/main.py` in the routers list
6. Tests: Add `tests/unit/test_comment_service.py`, `tests/integration/test_comments_api.py`
7. Migration: Run `uv run alembic revision --autogenerate -m "add comment table"`

**New Platform Adapter (e.g., TikTok):**
1. Create `src/smm/adapters/tiktok.py` subclassing `AbstractPlatformAdapter`
2. Implement `publish()` and `validate_token()` async methods
3. Register in `src/smm/adapters/registry.py`: `AdapterRegistry.register(Platform.TIKTOK, TikTokAdapter())`
4. Add `Platform.TIKTOK` enum value to `src/smm/models/social_account.py`
5. Tests: Add `tests/unit/test_tiktok_adapter.py`

**New React Component/Page:**
1. Create `src/client/src/pages/ComponentPage.tsx` or `src/client/src/components/Component.tsx`
2. Import in router if it's a page: `src/client/src/router.tsx`
3. Add route definition if needed
4. Use `api.get()`, `api.post()` from `src/client/src/lib/api.ts` for API calls
5. Check auth with `isAuthenticated()` from `src/client/src/lib/auth.ts`

**Shared Utilities:**
- Python: Add to `src/smm/utils.py` or create module-specific utility file
- TypeScript: Add to `src/client/src/lib/` for shared logic

## Special Directories

**`.planning/codebase/`:**
- Purpose: GSD (Getting Stuff Done) documentation generated by Claude
- Contains: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md
- Generated: Yes (created by `/gsd:map-codebase` command)
- Committed: Yes (checked into repo for reference)

**`alembic/versions/`:**
- Purpose: Database migration history
- Generated: Yes (created by `alembic revision --autogenerate`)
- Committed: Yes (critical for reproducible deployments)

**`tests/`:**
- Purpose: Automated test suite
- Generated: No (manually written and committed)
- Committed: Yes

**`src/client/public/`:**
- Purpose: Static assets served by Vite
- Generated: No
- Committed: Yes (contains favicon, etc.)

**`dist/`** (if present):
- Purpose: Built client bundle
- Generated: Yes (by `vite build`)
- Committed: No (in .gitignore)

**`.env`:**
- Purpose: Local environment configuration
- Generated: No (created manually per environment)
- Committed: No (in .gitignore; use .env.example as template)

**`node_modules/` and `.venv/`:**
- Purpose: Installed dependencies
- Generated: Yes (by `npm install`, `uv sync`)
- Committed: No (in .gitignore)
