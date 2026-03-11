# External Integrations

**Analysis Date:** 2026-03-11

## APIs & External Services

**Facebook Graph API (v19.0):**
- OAuth 2.0 authorization for connecting Facebook Pages and personal profiles
- Publishing posts to Facebook page feeds and personal timelines
- Retrieving user's connected pages and profile information
  - SDK/Client: httpx (async HTTP client)
  - Auth: OAuth 2.0 with long-lived tokens (60+ days)
  - Endpoints:
    - `https://www.facebook.com/v19.0/dialog/oauth` - Authorization dialog
    - `https://graph.facebook.com/v19.0/oauth/access_token` - Token exchange and refresh
    - `https://graph.facebook.com/v19.0/me/accounts` - Fetch managed pages
    - `https://graph.facebook.com/v19.0/me` - Fetch user profile
    - `https://graph.facebook.com/v19.0/{page_id}/feed` - Publish to page feed

**Instagram Graph API (v19.0):**
- Publishing photos/captions to Instagram Business accounts (via Facebook Graph API)
- Token validation for Instagram accounts
  - SDK/Client: httpx (async HTTP client)
  - Auth: Long-lived page access tokens from Facebook OAuth flow
  - Endpoints:
    - `https://graph.facebook.com/v19.0/{user_id}/media` - Create media container
    - `https://graph.facebook.com/v19.0/{user_id}/media_publish` - Publish media

## Data Storage

**Databases:**
- PostgreSQL 17 (primary)
  - Connection string: `postgresql+asyncpg://smm:smm@localhost:5434/smm`
  - Client: SQLAlchemy 2.x with asyncpg async driver
  - Migrations: Alembic (located in `alembic/` directory)

**Test Database:**
- PostgreSQL 17 (separate test instance on port 5433)
  - Connection string: `postgresql+asyncpg://smm:smm@localhost:5433/smm_test`
  - Automatically recreated per test via pytest fixture

**File Storage:**
- Not externally integrated - image URLs are stored as strings in database
- Client: Frontend sends image_url to backend, adapter calls external APIs

**Caching:**
- Redis 7-alpine (message broker, not caching layer)
  - Connection: `redis://localhost:6379/0`
  - Purpose: Dramatiq task queue backend only

## Authentication & Identity

**API Auth Provider:** Custom JWT-based
- Implementation: python-jose with HS256 algorithm
- Token creation: `create_access_token()` in `src/smm/services/auth.py`
- Token validation: `get_current_user` dependency in `src/smm/dependencies.py`
- Storage: Bearer token in Authorization header, JWT in localStorage (frontend)
- Expiration: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)

**Social Account Authentication:** OAuth 2.0
- Facebook OAuth 2.0 for connecting social accounts
- User authorizes app at Facebook → receives short-lived token → exchanged for long-lived token
- Long-lived tokens stored in `SocialAccount` model with optional expiration
- Flow implemented in `src/smm/services/facebook_oauth.py` and `src/smm/api/v1/oauth.py`

## Monitoring & Observability

**Error Tracking:**
- Not integrated - relies on application logs and HTTP error responses

**Logs:**
- Standard Python logging via `logging` module
- APScheduler logs scheduler polling activity
- Dramatiq worker logs task execution
- Log level: INFO by default (DEBUG available in development)

## CI/CD & Deployment

**Hosting:**
- Docker-based (Docker Compose for local development)
- Dockerfile provided for containerization
- Environment-based configuration via `.env` file

**CI Pipeline:**
- Not detected - no GitHub Actions, GitLab CI, or similar found

## Environment Configuration

**Required env vars for backend:**
- `DATABASE_URL` - PostgreSQL connection string
- `TEST_DATABASE_URL` - Test database connection string
- `REDIS_URL` - Redis broker connection
- `SECRET_KEY` - JWT signing key (must be cryptographically random in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token lifetime (default: 30)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `BASE_URL` - Application base URL for OAuth redirects (e.g., http://localhost:8000)
- `FACEBOOK_APP_ID` - OAuth app ID from Facebook Developers console
- `FACEBOOK_APP_SECRET` - OAuth app secret from Facebook Developers console

**Secrets location:**
- `.env` file (not committed, see `.gitignore`)
- `.env.example` provides template for required variables
- Backend loads via Pydantic Settings with `env_file: ".env"`

## Webhooks & Callbacks

**Incoming:**
- `GET /api/v1/oauth/facebook/callback` - Facebook OAuth redirect after user authorization
  - Query params: `code` (authorization code), `state` (CSRF token)
  - Returns: List of user's Facebook Pages or confirmation of profile connection

**Outgoing:**
- Not implemented - application does not send webhooks to external services
- One-directional: app calls Facebook Graph API, Instagram Graph API only

## Data Flow: Post Publishing

**Request Path:**
1. User schedules post via `POST /api/v1/posts` (frontend → backend)
2. Backend stores post as DRAFT, creates PostTarget for each social account (SCHEDULED status)
3. APScheduler polls every 30s for targets where `status=SCHEDULED AND scheduled_at<=now()`
4. Atomically transitions targets to PUBLISHING status and enqueues Dramatiq tasks
5. Dramatiq worker picks up task from Redis, resolves platform adapter, calls `adapter.publish()`
6. Adapter calls Facebook/Instagram Graph API with post content and access token
7. Worker updates PostTarget to PUBLISHED or FAILED based on API response
8. Frontend polls `GET /api/v1/posts` to fetch updated post status

**Error Handling:**
- Token validation failure → API returns 400 Bad Request
- OAuth state expiration → API returns 400 Bad Request (10 min max)
- Facebook API errors → Worker retries up to 3 times with exponential backoff
- Adapter exceptions → PostTarget marked as FAILED, user can retry manually

---

*Integration audit: 2026-03-11*
