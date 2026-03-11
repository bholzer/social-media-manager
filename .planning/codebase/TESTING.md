# Testing Patterns

**Analysis Date:** 2026-03-11

## Test Framework

**Runner:**
- pytest 8.0.0+
- pytest-asyncio 0.24.0+ with `asyncio_mode = "auto"` (no `@pytest.mark.asyncio` decorator needed)
- Config: `pyproject.toml` [tool.pytest.ini_options]

**Assertion Library:**
- pytest built-in assertions: `assert`, `assert response.status_code == 201`
- pytest-raises for exception testing: `pytest.raises()`

**Run Commands:**
```bash
uv run pytest                              # Run all tests
uv run pytest tests/unit/                  # Unit tests only
uv run pytest tests/integration/           # Integration tests only
uv run pytest tests/unit/test_models.py::TestUserModel::test_create_user  # Single test
uv run pytest --cov=smm                    # With coverage
uv run pytest -x                           # Stop on first failure
uv run pytest -v                           # Verbose output
```

## Test File Organization

**Location:**
- Separate directory: `tests/` at project root
- Not co-located with source code
- Organized into `unit/`, `integration/`, `e2e/` subdirectories

**Naming:**
- `test_*.py` prefix: `test_models.py`, `test_auth_service.py`, `test_adapters.py`
- Test functions: `test_*` prefix: `test_create_user`, `test_user_email_unique`
- Test classes: `Test*` prefix: `TestUserModel`, `TestPostCRUD`, `TestJWT`

**Structure:**
```
tests/
├── conftest.py              # Pytest fixtures (test_engine, setup_database, session, client, authenticated_client)
├── factories.py             # FactoryBoy factories for test data
├── unit/
│   ├── test_models.py       # ORM model tests
│   ├── test_schemas.py      # Pydantic schema tests
│   ├── test_auth_service.py # Auth service tests
│   ├── test_adapters.py     # Adapter registry tests
│   ├── test_publisher.py    # Publisher service with mocking
│   └── test_facebook_oauth.py
├── integration/
│   ├── test_auth_endpoints.py   # API endpoint tests
│   ├── test_posts.py            # Post CRUD endpoint tests
│   ├── test_social_accounts.py
│   ├── test_scheduler.py
│   └── test_oauth.py
└── e2e/
    └── test_publish_flow.py     # Full workflow end-to-end tests
```

## Test Structure

**Suite Organization:**
```python
# From tests/integration/test_posts.py
class TestPostCRUD:
    async def _create_account(self, client):
        """Helper method (private, starts with _)."""
        resp = await client.post(
            "/api/v1/social-accounts/",
            json={...},
        )
        return resp.json()["id"]

    async def test_create_post(self, authenticated_client):
        """Test method (public, starts with test_)."""
        account_id = await self._create_account(authenticated_client)
        response = await authenticated_client.post(...)
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Hello world!"
```

**Patterns:**
- Test classes group related tests
- Setup/helper methods prefixed with `_` (private convention)
- Each test method has single clear assertion or group of related assertions
- Tests use fixtures injected as parameters: `async def test_create_user(self, session):`
- Async tests defined with `async def` (auto-detected, no decorator needed)

## Mocking

**Framework:** unittest.mock (built-in)

**Patterns:**
```python
# From tests/unit/test_publisher.py
from unittest.mock import AsyncMock, patch

@patch("smm.services.publisher.AdapterRegistry")
async def test_publish_success(self, mock_registry, session):
    target = await self._setup(session)

    mock_adapter = AsyncMock()
    mock_adapter.publish.return_value = PublishResult(platform_post_id="post_123")
    mock_registry.get.return_value = mock_adapter

    await publish_target(session, target.id)

    # Verify mock was called
    assert target.status == PostTargetStatus.PUBLISHED

# From tests/e2e/test_publish_flow.py
@patch("smm.workers.tasks.publish_target_task")
async def test_full_publish_flow(self, mock_task, client):
    # ... test code ...
    mock_task.send.assert_called_once()
```

**What to Mock:**
- External services: `smm.workers.tasks.publish_target_task` (Dramatiq)
- Platform adapters: `smm.adapters.registry.AdapterRegistry`
- External API calls

**What NOT to Mock:**
- Database operations (use test database)
- ORM models
- Pydantic schemas
- Service business logic
- FastAPI dependencies (use fixtures to override)

## Fixtures and Factories

**Test Data Factories:**
```python
# From tests/factories.py
class UserFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.LazyFunction(fake.email)
    hashed_password = factory.LazyFunction(lambda: hash_password("testpassword123"))

class PostFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.LazyFunction(uuid.uuid4)
    content = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    scheduled_at = None
```

**Pytest Fixtures:**
```python
# From tests/conftest.py
@pytest.fixture(autouse=True)
async def setup_database(test_engine):
    """Runs before every test (autouse=True)."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides AsyncClient for testing FastAPI app."""
    from smm.main import app
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(...) as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
async def authenticated_client(client: AsyncClient):
    """Registers user and sets Bearer token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
```

**Location:**
- `tests/conftest.py`: Core fixtures shared across all tests
- `tests/factories.py`: FactoryBoy factories for creating test data dicts
- Test-specific fixtures: Defined in test file itself if only used once

## Coverage

**Requirements:** Not enforced (no threshold in pyproject.toml)

**View Coverage:**
```bash
uv run pytest --cov=smm
uv run pytest --cov=smm --cov-report=html   # HTML report in htmlcov/
```

**Coverage file:** `.coverage` exists in repo root

## Test Types

### Unit Tests (`tests/unit/`)

**Scope:** Individual functions, classes, and components in isolation

**Approach:**
- Test ORM models: CRUD, relationships, cascading deletes
- Test business logic: Password hashing, JWT creation/decoding
- Test adapters and registries
- Use mocks for external dependencies

**Examples:**
- `test_models.py`: Tests model creation, constraints, relationships
- `test_auth_service.py`: Tests password hashing, JWT encode/decode
- `test_adapters.py`: Tests adapter registry lookup

### Integration Tests (`tests/integration/`)

**Scope:** API endpoints with real database and authentication

**Approach:**
- Use real database (test instance at `localhost:5433`)
- Test full request/response cycle
- Test cross-layer interactions: routes → services → models
- Test validation and error handling
- Mock external services (platform APIs)

**Examples:**
- `test_auth_endpoints.py`: Register, login, get current user
- `test_posts.py`: Post CRUD via HTTP
- `test_social_accounts.py`: Social account endpoints
- `test_scheduler.py`: Scheduler integration

### E2E Tests (`tests/e2e/`)

**Scope:** Full user workflows end-to-end

**Approach:**
- Tests multiple steps: register → link account → create post → publish
- Mocks only truly external systems (worker tasks)
- Verifies complete data flow

**Examples:**
- `test_publish_flow.py`: Register, link account, create post, trigger publish

## Common Patterns

### Async Testing

```python
# No @pytest.mark.asyncio needed - asyncio_mode = "auto"
class TestPostModel:
    async def test_create_post_with_targets(self, session):
        user = User(email="post@test.com", hashed_password="h")
        session.add(user)
        await session.commit()
        # ... test continues ...
        await session.refresh(post)
        assert post.id is not None
```

### Error Testing

```python
# Database constraint violations
async def test_user_email_unique(self, session):
    import sqlalchemy

    user1 = User(email="dup@test.com", hashed_password="h1")
    user2 = User(email="dup@test.com", hashed_password="h2")
    session.add(user1)
    await session.commit()
    session.add(user2)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        await session.commit()

# API error responses
async def test_create_post_invalid_account(self, authenticated_client):
    response = await authenticated_client.post(
        "/api/v1/posts/",
        json={
            "content": "Bad target",
            "targets": [{"social_account_id": str(uuid.uuid4())}],
        },
    )
    assert response.status_code == 400

# Service ValueError → HTTP 400
# Routes catch ValueError and convert to HTTPException(status_code=400, detail=str(e))
```

### Database Setup and Cleanup

**Per-Test Reset:**
```python
# setup_database fixture (autouse=True) runs before every test:
# 1. Drops all tables
# 2. Creates all tables
# 3. Yields (test runs)
# 4. Drops all tables again

# This ensures complete isolation: no cross-test data contamination
```

### API Testing Pattern

```python
# Typical integration test flow
async def test_create_post(self, authenticated_client):
    # Setup: create prerequisite (social account)
    account_id = await self._create_account(authenticated_client)

    # Action: make API call
    response = await authenticated_client.post(
        "/api/v1/posts/",
        json={"content": "Hello world!", "targets": [{"social_account_id": account_id}]},
    )

    # Assert: check response
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hello world!"
    assert len(data["targets"]) == 1
```

### Mock Patterns

```python
# Patch a class and return a mock instance
@patch("smm.services.publisher.AdapterRegistry")
async def test_publish_success(self, mock_registry, session):
    mock_adapter = AsyncMock()
    mock_adapter.publish.return_value = PublishResult(platform_post_id="post_123")
    mock_registry.get.return_value = mock_adapter

    # When publish_target calls AdapterRegistry.get(), it returns mock_adapter
    await publish_target(session, target.id)

# Patch a task (Dramatiq)
@patch("smm.workers.tasks.publish_target_task")
async def test_full_publish_flow(self, mock_task, client):
    # ... trigger publish endpoint ...
    mock_task.send.assert_called_once()  # Verify Dramatiq task was enqueued
```

## Test Dependencies

From `pyproject.toml`:
- pytest>=8.0.0
- pytest-asyncio>=0.24.0
- pytest-factoryboy>=2.7.0 (automatically registers factories as fixtures)
- pytest-cov>=6.0.0 (coverage)
- faker>=33.0.0 (fake data generation)
- factory (via pytest-factoryboy) for FactoryBoy

## Special Configurations

**Pytest Settings (pyproject.toml):**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"                    # Auto-detect async tests
testpaths = ["tests"]                    # Where to find tests
pythonpath = ["src"]                     # Add src to path for imports
filterwarnings = ["ignore::DeprecationWarning"]  # Ignore deprecation warnings
```

**Database Isolation:**
- Test database separate from main: `test_database_url = postgresql://... :5433/...`
- Main database on port 5434
- Each test runs with clean database (drop/create in setup_database fixture)

---

*Testing analysis: 2026-03-11*
