# Architecture

**Analysis Date:** 2026-03-11

## Pattern Overview

**Overall:** Three-tier async architecture with layered separation of concerns (API → Services → Models).

**Key Characteristics:**
- Async-first Python backend using FastAPI + SQLAlchemy 2.x with asyncpg
- Distributed task queue (Dramatiq + Redis) for post publishing workloads
- APScheduler polling for scheduled post detection and task enqueueing
- Platform-agnostic adapter pattern for multi-platform social media publishing
- Multi-user isolation via user_id scoping on all queries
- Separate React client (Vite + TypeScript) for frontend UI

## Layers

**API Layer (Routes):**
- Purpose: HTTP request/response handling, authentication, parameter validation
- Location: `src/smm/api/v1/`
- Contains: Router handlers for auth, posts, social accounts, users, OAuth flows
- Depends on: Services, Schemas, Dependencies
- Used by: HTTP clients (React frontend)
- Pattern: Each resource has a router file (auth.py, posts.py, social_accounts.py); handlers extract current_user and session via dependencies; business logic errors (ValueError) converted to 400 HTTP responses

**Service Layer:**
- Purpose: Business logic, database queries, state transitions, validations
- Location: `src/smm/services/`
- Contains: PostService, AuthService, FacebookOAuthService, PublisherService
- Depends on: Models, Schemas, Adapters, Database
- Used by: API routes, Workers
- Pattern: Services accept AsyncSession and parameters; raise ValueError for business rule violations; handle transaction commits/rollbacks

**Model Layer (ORM):**
- Purpose: Database schema definition, relationships, constraints
- Location: `src/smm/models/`
- Contains: User, Post, PostTarget, SocialAccount (all inherit from Base)
- Depends on: SQLAlchemy, UUID generation
- Used by: Services via queries
- Pattern: SQLAlchemy 2.x mapped classes with UUID primary keys and server defaults

**Schema Layer (Validation):**
- Purpose: Request/response validation, serialization
- Location: `src/smm/schemas/`
- Contains: Pydantic models for auth (LoginRequest, RegisterRequest, TokenResponse), posts (PostCreate, PostUpdate, PostResponse), social accounts
- Depends on: Pydantic
- Used by: API routes for request validation and response marshaling
- Pattern: Separate from ORM models; PostCreate includes nested targets; PostResponse includes related targets

**Database Layer:**
- Purpose: Connection pooling, session factory, engine configuration
- Location: `src/smm/database.py`
- Contains: async_session_factory, engine creation
- Depends on: SQLAlchemy async, Config
- Used by: Services, Workers, Dependencies

**Adapter Layer (Platform Integration):**
- Purpose: Abstract social platform API calls, provide consistent interface for publishing
- Location: `src/smm/adapters/`
- Contains: AbstractPlatformAdapter (base class), FacebookAdapter, InstagramAdapter, AdapterRegistry
- Depends on: External platform APIs
- Used by: Publisher service
- Pattern: Strategy pattern via abstract base; AdapterRegistry maps Platform enum to adapter instance; add new platforms by creating adapter and registering it

**Worker Layer (Async Tasks):**
- Purpose: Background post publishing via Dramatiq message queue
- Location: `src/smm/workers/`
- Contains: publish_target_task (Dramatiq actor with retry logic), _publish async helper
- Depends on: Services, Dramatiq broker, AsyncSession
- Used by: APScheduler and API endpoints
- Pattern: Dramatiq actor wrapping async function; re-checks target status before publishing (double-publish prevention)

**Scheduler Layer (Polling):**
- Purpose: Periodic detection and enqueueing of scheduled posts
- Location: `src/smm/scheduler/scheduler.py`
- Contains: poll_and_enqueue job, start_scheduler, stop_scheduler
- Depends on: APScheduler, Database, Workers
- Used by: FastAPI lifespan (started on app startup)
- Pattern: APScheduler BackgroundScheduler polls every 30s; finds targets with status=SCHEDULED and post.scheduled_at <= now; atomically transitions to PUBLISHING; enqueues Dramatiq tasks; runs in app process

## Data Flow

**Post Creation:**
1. Client sends POST /api/v1/posts with PostCreate payload (content, targets array)
2. PostsAPI.create_post → PostService.create validates target ownership → creates Post record → creates PostTarget records (status=DRAFT or SCHEDULED based on scheduled_at) → returns Post with targets populated

**Post Publishing (Scheduled):**
1. APScheduler polls every 30s via poll_and_enqueue()
2. Finds PostTargets where status=SCHEDULED and Post.scheduled_at <= now
3. Atomically transitions targets to PUBLISHING status
4. Enqueues publish_target_task(target_id) to Dramatiq/Redis for each target
5. Dramatiq worker picks up task (separate process)
6. Worker calls publish_target service → resolves adapter via AdapterRegistry → calls adapter.publish() → updates target to PUBLISHED with platform_post_id
7. On adapter error → target status set to FAILED with error_message
8. Client polls /api/v1/posts/{post_id} to see updated target statuses

**Post Publishing (Manual/Immediate):**
1. Client sends POST /api/v1/posts/{post_id}/publish-now
2. PostsAPI.publish_now transitions draft/scheduled targets to PUBLISHING
3. Commits to DB
4. Enqueues Dramatiq tasks for each target
5. Same worker flow as scheduled publishing

**User Authentication:**
1. Client sends POST /api/v1/auth/register or /api/v1/auth/login
2. Service hashes password (bcrypt) or validates password
3. Creates or retrieves User record
4. Generates JWT access token (HS256)
5. Returns TokenResponse with token
6. Client stores token in localStorage
7. Subsequent requests include Authorization: Bearer {token}
8. get_current_user dependency decodes token → queries User by ID → raises 401 if invalid or missing

**State Management:**
- Database is single source of truth (PostgreSQL)
- Session-based state in API layer via AsyncSession dependency
- No client-side state management library (React state local to components)
- Token stored in localStorage on client

## Key Abstractions

**PostTargetStatus (State Machine):**
- Purpose: Tracks publishing lifecycle of a single target
- Examples: `src/smm/models/post_target.py`
- Pattern: StrEnum with states DRAFT → SCHEDULED → PUBLISHING → (PUBLISHED | FAILED)
- Transitions: manual (DRAFT to PUBLISHING via API), automatic (SCHEDULED to PUBLISHING via scheduler), terminal (to FAILED on adapter error)

**Platform (Social Account Type):**
- Purpose: Identify which social platform a SocialAccount represents
- Examples: `src/smm/models/social_account.py`, Platform enum
- Pattern: StrEnum (FACEBOOK, INSTAGRAM, TWITTER, LINKEDIN) for type safety and database serialization
- Used by: AdapterRegistry to route to correct adapter

**AbstractPlatformAdapter:**
- Purpose: Define contract for platform-specific publishing logic
- Examples: `src/smm/adapters/base.py`, `src/smm/adapters/facebook.py`, `src/smm/adapters/instagram.py`
- Pattern: ABC with async publish() and validate_token() methods; returns PublishResult with platform_post_id
- Extensibility: Add new platform by subclassing and registering in AdapterRegistry

**User Multi-Tenancy:**
- Purpose: Isolate data across users
- Pattern: All queries and mutations scope to current_user.id; User has cascade delete on posts and social_accounts; enforced at service layer
- Example: PostService.get filters on user_id; PostService.list only returns current user's posts

## Entry Points

**FastAPI Application:**
- Location: `src/smm/main.py`
- Triggers: `uv run uvicorn smm.main:app --reload`
- Responsibilities: Create FastAPI app, register routers (auth, users, posts, social_accounts, oauth), start/stop APScheduler via lifespan context

**Dramatiq Worker:**
- Location: `src/smm/workers/tasks.py`
- Triggers: `uv run dramatiq smm.workers.tasks` (separate process)
- Responsibilities: Register Redis broker, pick up publish_target_task messages, execute async publishing logic

**React Client Entry:**
- Location: `src/client/src/main.tsx`
- Triggers: `npm run dev` (Vite dev server) or browser loads built assets
- Responsibilities: Mount React app, set up router, initialize auth state check

## Error Handling

**Strategy:** Three-level error handling

**API Layer Patterns:**
- Services raise ValueError for business logic violations → routes catch and return 400 HTTP responses
- IntegrityError (duplicate email) caught in registration → 409 Conflict
- Resource not found returns 404
- Authentication failures return 401
- Unexpected exceptions logged and return 500

**Service Layer Patterns:**
- ValueError raised for invalid state transitions (e.g., "Cannot update a post with published targets")
- ValueError raised for authorization violations (e.g., "One or more social accounts not found or not owned by user")
- Errors propagate to caller (route handler) for HTTP conversion

**Worker/Publisher Layer Patterns:**
- Adapter exceptions caught in publish_target; target status set to FAILED with error_message
- Dramatiq retry logic (max_retries=3, exponential backoff 1s to 60s) attempts retry on task exceptions
- No HTTP response; state persisted to database for client polling

## Cross-Cutting Concerns

**Logging:** Standard Python logging module; configured at module level (e.g., `logger = logging.getLogger(__name__)`); used in scheduler and services for job enqueueing and errors

**Validation:** Pydantic schemas validate all API input (email format, UUID types, nested objects); ORM models define database constraints (unique indexes, FK constraints)

**Authentication:** JWT-based (HS256 algorithm); token issued on register/login; validated on protected endpoints via get_current_user dependency; token includes user ID claim; no refresh tokens implemented (30-minute expiration via access_token_expire_minutes)

**Authorization:** User-scoped queries in all services (filter on user_id); prevents users accessing other users' data at query level, not endpoint level

**Async/Await:** All DB operations are async (AsyncSession, asyncpg); all routes are async; workers wrap async logic in sync Dramatiq actors via asyncio.run()
