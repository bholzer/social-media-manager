# Refactoring Analysis

Deep analysis of the social-media-manager codebase identifying shortcomings, anti-patterns, and refactoring opportunities.

## Overall Assessment

The codebase has a clean layered architecture (Routes → Services → Models) with good separation of concerns, proper async patterns, and solid test coverage (~91 tests). The issues below are refinements, not fundamental problems.

---

## Completed Refactorings

### 1. Extract `SocialAccountService` (Architectural Inconsistency)

**Problem:** `api/v1/social_accounts.py` had raw SQLAlchemy queries inline in every route handler, while `api/v1/posts.py` properly delegated to `PostService`. The "fetch account by id + user_id, return 404 if missing" pattern was copy-pasted 3 times.

**Fix:** Created `services/social_account.py` with a `SocialAccountService` class mirroring `PostService`. Routes now delegate all query logic to the service.

---

### 2. Narrow Broad Exception Handling

**Problem:** Several places caught bare `Exception` when a specific type was appropriate.

- `api/v1/auth.py` caught `Exception` instead of `sqlalchemy.exc.IntegrityError` — any unexpected error silently became a 409 Conflict.
- `api/v1/oauth.py` caught `Exception` instead of `httpx.HTTPError` in 4 places — a bug in serialization code would appear as "Facebook token exchange failed" instead of surfacing the real error.

**Fix:** Narrowed to `IntegrityError` in auth and `httpx.HTTPError` in oauth.

---

### 3. Remove Duplicate `get_session()` Definition

**Problem:** Both `database.py` and `dependencies.py` defined identical `get_session()` async generators. All routes imported from `dependencies.py`; the `database.py` version was unused dead code.

**Fix:** Removed `get_session()` from `database.py`.

---

### 4. Extract Shared Facebook Graph API Base URL

**Problem:** Three files hardcoded `"https://graph.facebook.com/v19.0"`:
- `adapters/facebook.py`
- `adapters/instagram.py`
- `services/facebook_oauth.py`

When Facebook bumps their API version, all three needed updating.

**Fix:** Created `adapters/constants.py` with `GRAPH_API_BASE_URL` and updated all three files to import from it.

---

## Remaining Opportunities

### 5. Structured Error Responses

**Problem:** Routes raise `HTTPException(detail=str(e))` with plain strings. No consistent error schema means clients must string-match to understand errors.

**Pattern:**
```python
class ErrorResponse(BaseModel):
    error_code: str    # machine-readable: "account_not_found", "invalid_token"
    message: str       # human-readable
```

**Effort:** Medium | **Value:** High | **Risk:** Medium (API contract change)

---

### 6. Pagination Metadata on List Endpoints

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

### 7. Request Logging Middleware

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

### 8. Error Path Test Gaps

Tests cover happy paths well but `services/facebook_oauth.py` has no tests for network failures, malformed API responses, or timeouts. The publisher tests don't cover unexpected adapter exceptions beyond the basic failure case.

**Effort:** Medium | **Value:** Medium | **Risk:** None

---

## Summary Table

| # | Refactoring | Status |
|---|------------|--------|
| 1 | Extract `SocialAccountService` | Done |
| 2 | Narrow exception handling | Done |
| 3 | Remove duplicate `get_session()` | Done |
| 4 | Extract shared Graph API constant | Done |
| 5 | Structured error responses | Future |
| 6 | Pagination metadata | Future |
| 7 | Request logging middleware | Future |
| 8 | Error path test coverage | Future |
