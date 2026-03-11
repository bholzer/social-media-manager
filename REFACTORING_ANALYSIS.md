# Refactoring Analysis

Deep analysis of the social-media-manager codebase identifying shortcomings, anti-patterns, and high-value refactoring opportunities.

## Overall Assessment

The codebase has a clean layered architecture (Routes → Services → Models) with good separation of concerns, proper async patterns, and solid test coverage (~91 tests). The issues below are refinements, not fundamental problems.

---

## High-Value, Low-Effort Refactoring Candidates

### 1. Extract `SocialAccountService` (Architectural Inconsistency)

**Problem:** `api/v1/social_accounts.py` has raw SQLAlchemy queries inline in every route handler, while `api/v1/posts.py` properly delegates to `PostService`. The "fetch account by id + user_id, return 404 if missing" pattern is copy-pasted 3 times.

**Location:** `src/smm/api/v1/social_accounts.py` (lines 43, 55, 75)

**Fix:** Create `services/social_account.py` with a `SocialAccountService` class mirroring `PostService`:

```python
class SocialAccountService:
    def __init__(self, session: AsyncSession, user_id: UUID):
        self.session = session
        self.user_id = user_id

    async def get(self, account_id: UUID) -> SocialAccount | None:
        result = await self.session.execute(
            select(SocialAccount).where(
                SocialAccount.id == account_id,
                SocialAccount.user_id == self.user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(self) -> list[SocialAccount]:
        ...

    async def create(self, data: SocialAccountCreate) -> SocialAccount:
        ...

    async def delete(self, account_id: UUID) -> None:
        ...
```

**Effort:** Low | **Value:** High | **Risk:** Low

---

### 2. Narrow Broad Exception Handling

**Problem:** Several places catch bare `Exception` when a specific type is appropriate.

**Locations:**

- `src/smm/api/v1/auth.py:17` — catches `Exception` instead of `sqlalchemy.exc.IntegrityError`:
  ```python
  # Current (bad): hides any unexpected error as a 409 Conflict
  except Exception:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

  # Fixed: only catches actual duplicate key violations
  except IntegrityError:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
  ```

- `src/smm/api/v1/oauth.py` (lines ~88, 100, 112, 156) — catches `Exception` instead of `httpx.HTTPError`. A serialization bug in your code would appear as "Facebook token exchange failed" instead of surfacing the real error.

**Effort:** Low | **Value:** High | **Risk:** Low

---

### 3. Move OAuth State from In-Memory Dict to Redis

**Problem:** `api/v1/oauth.py:26` stores OAuth CSRF state in a module-level `dict`:
```python
_oauth_states: dict[str, dict] = {}
```

Issues:
- **Lost on restart** — user starts OAuth, server restarts, callback silently fails
- **Doesn't work with multiple instances** — state created on instance A, callback hits instance B
- **Memory leak** — expired entries are never cleaned up

**Fix:** Store state in Redis (already in the infrastructure) with a 10-minute TTL:
```python
await redis.setex(f"oauth_state:{state}", 600, json.dumps({"user_id": str(user_id)}))
```

**Effort:** Low | **Value:** High | **Risk:** Low

---

### 4. Remove Duplicate `get_session()` Definition

**Problem:** Both `database.py:11` and `dependencies.py:16` define identical `get_session()` async generators. All routes import from `dependencies.py`; the `database.py` version is unused dead code.

**Fix:** Remove `get_session()` from `database.py`.

**Effort:** Trivial | **Value:** Medium | **Risk:** None

---

### 5. Extract Shared Facebook Graph API Base URL

**Problem:** Both adapters hardcode the same constant:
- `adapters/facebook.py:7` → `BASE_URL = "https://graph.facebook.com/v19.0"`
- `adapters/instagram.py:7` → `BASE_URL = "https://graph.facebook.com/v19.0"`
- `services/facebook_oauth.py` also uses Graph API URLs with the version embedded

When Facebook bumps their API version, you need to update 3 files.

**Fix:** Add `facebook_graph_api_url` to `config.py` or create a shared constant:
```python
# adapters/constants.py
GRAPH_API_BASE_URL = "https://graph.facebook.com/v19.0"
```

**Effort:** Trivial | **Value:** Medium | **Risk:** None

---

## Patterns Worth Implementing

### 6. Structured Error Responses

**Problem:** Routes raise `HTTPException(detail=str(e))` with plain strings. No consistent error schema means clients must string-match to understand errors.

**Pattern:**
```python
class ErrorResponse(BaseModel):
    error_code: str    # machine-readable: "account_not_found", "invalid_token"
    message: str       # human-readable

# Usage in routes:
raise HTTPException(
    status_code=404,
    detail=ErrorResponse(error_code="account_not_found", message="...").model_dump()
)
```

**Effort:** Medium | **Value:** High | **Risk:** Medium (API contract change)

---

### 7. Pagination Metadata on List Endpoints

**Problem:** `PostService.list()` accepts `skip`/`limit` but returns bare lists. Clients can't determine total count or whether more pages exist.

**Pattern:**
```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool
```

**Effort:** Low | **Value:** Medium | **Risk:** Low (additive API change)

---

### 8. Request Logging Middleware

**Problem:** No request/response logging. Zero observability into request patterns, latency, or error rates in production.

**Pattern:**
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")
    return response
```

**Effort:** Low | **Value:** Medium | **Risk:** None

---

## Lower-Priority Issues

### 9. `asyncio.run()` in Dramatiq Worker

`workers/tasks.py` bridges sync Dramatiq with async code by calling `asyncio.run()` per task, which creates and destroys an event loop each time. This works but is wasteful. Consider a persistent loop or `dramatiq-asyncio`.

### 10. Error Path Test Gaps

Tests cover happy paths well but `services/facebook_oauth.py` has no tests for network failures, malformed API responses, or timeouts. The publisher tests don't cover unexpected adapter exceptions beyond the basic failure case.

---

## Summary Table

| # | Refactoring | Effort | Value | Risk |
|---|------------|--------|-------|------|
| 1 | Extract `SocialAccountService` | Low | High | Low |
| 2 | Narrow exception handling | Low | High | Low |
| 3 | Move OAuth state to Redis | Low | High | Low |
| 4 | Remove duplicate `get_session()` | Trivial | Medium | None |
| 5 | Extract shared Graph API constant | Trivial | Medium | None |
| 6 | Structured error responses | Medium | High | Medium |
| 7 | Pagination metadata | Low | Medium | Low |
| 8 | Request logging middleware | Low | Medium | None |
| 9 | Fix `asyncio.run()` in worker | Medium | Low | Medium |
| 10 | Error path test coverage | Medium | Medium | None |

Items 1–5 are the highest-ROI quick wins. Items 6–8 are worth planning. Items 9–10 are lower priority.
