# Coding Conventions

**Analysis Date:** 2026-03-11

## Python Backend Conventions

### Naming Patterns

**Files:**
- `snake_case` for module names: `post.py`, `auth.py`, `publisher.py`
- Organized by layer: `models/`, `services/`, `schemas/`, `api/v1/`, `adapters/`, `workers/`

**Classes:**
- `PascalCase` for all classes: `Post`, `User`, `SocialAccount`, `PostTarget`, `AbstractPlatformAdapter`, `ApiError`
- Enum classes also `PascalCase`: `PostTargetStatus`, `Platform`

**Functions:**
- `snake_case` for all functions: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`, `publish_target`
- Async functions use `async def` syntax (no special naming convention)

**Variables:**
- `snake_case` for local variables and parameters: `user_id`, `access_token`, `post_content`
- Constants use `SCREAMING_SNAKE_CASE` (if used)

**Types:**
- Python 3.12+ union syntax: `str | None`, `list[Post]`, not `Optional[str]` or `List[Post]`
- SQLAlchemy `Mapped` types with full type hints: `Mapped[uuid.UUID]`, `Mapped[str]`, `Mapped[datetime.datetime | None]`

### Code Style

**Formatting:**
- Ruff auto-formatter enforced via `uv run ruff format src/ tests/`
- Target Python 3.12+
- Line length: implicit from ruff defaults (88 characters typical)

**Linting:**
- Ruff with rules: `E`, `F`, `I`, `N`, `W`, `UP`
  - `E`: pycodestyle errors
  - `F`: Pyflakes (unused imports, undefined names)
  - `I`: isort (import ordering)
  - `N`: pep8-naming (naming conventions)
  - `W`: pycodestyle warnings
  - `UP`: pyupgrade (modern Python syntax)

**Import Organization:**
```python
# Order enforced by ruff isort:
# 1. Standard library
import datetime
import uuid
from collections.abc import AsyncGenerator

# 2. Third-party libraries
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# 3. Local project imports (first-party: "smm")
from smm.models.post import Post
from smm.services.post import PostService
```

**Path Aliases:**
- No path aliases used in Python code
- Explicit absolute imports from `smm` package

### Error Handling

**Patterns:**
- Services raise `ValueError` for business rule violations
- Routes catch `ValueError` and convert to HTTP 400 (Bad Request) responses
- HTTP exceptions use FastAPI's `HTTPException` with explicit `status_code` and `detail`
- Database integrity errors (e.g., unique constraint violations) propagate as `sqlalchemy.exc.IntegrityError` and are caught in tests

**Examples:**
```python
# Service layer - raises ValueError
async def create(self, user_id: uuid.UUID, data: PostCreate) -> Post:
    valid_accounts = {a.id for a in result.scalars().all()}
    if len(valid_accounts) != len(account_ids):
        raise ValueError("One or more social accounts not found or not owned by user")

# Route layer - converts to HTTP 400
try:
    post = await service.create(current_user.id, data)
except ValueError as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Not found responses
if post is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
```

### Logging

**Framework:** `print()` and standard Python logging (no structured logging library detected)

**Patterns:**
- Minimal logging in codebase
- Error messages embedded in exception strings or database columns (`error_message` field in `PostTarget`)

### Comments

**When to Comment:**
- Comments used minimally; code is self-documenting
- Docstrings used in abstract classes and complex business logic
- Inline comments for non-obvious decisions (e.g., "Double-publish prevention: re-check status" in `publisher.py`)

**Docstrings:**
- Not consistently applied; some functions have docstrings, most don't
- No formal docstring format (Google/NumPy style) enforced

### Function Design

**Size:** Functions are concise and focused
- Service methods: 5-50 lines typical
- Route handlers: 10-30 lines
- Utility functions: 2-15 lines

**Parameters:**
- Explicit parameter passing (no **kwargs globals)
- Dependencies injected via FastAPI `Depends()` in route handlers
- Session passed as first parameter to service methods: `def __init__(self, session: AsyncSession)`

**Return Values:**
- Single return type per function (no union returns except `None`)
- Services return model instances or `None`
- Routes return Pydantic schema instances
- Functions returning tuples: `tuple[list[Post], int]` (posts, total count)

### Module Design

**Exports:**
- Explicit imports; no `from module import *`
- Models defined in `models/` package, imported as `from smm.models.post import Post`

**Barrel Files:**
- `__init__.py` files exist but import selectively
- Example: `models/__init__.py` imports `Base` but not individual models

### SQLAlchemy 2.0 Async Patterns

**ORM Models:**
- Inherit from `Base` (declarative base)
- Use `Mapped` type annotations: `user_id: Mapped[uuid.UUID]`
- Use `mapped_column()` for column definitions
- UUID primary keys with server default: `server_default=text("gen_random_uuid()")`
- Timestamps with timezone: `DateTime(timezone=True)`
- Relationships: `relationship("User", back_populates="posts")`
- Cascade delete: `cascade="all, delete-orphan"`

**Queries:**
- Use `select()` query builder, not legacy ORM `.query()`
- Use `selectinload()` for eager loading relationships
- Use `.where()` for filtering
- Use `.scalar_one_or_none()` for single object retrieval
- Use `.scalars().all()` for multiple objects
- Use `.execute()` and await it: `result = await self.session.execute(query)`

**Enums:**
- Use `StrEnum` for string-based enums: `class PostTargetStatus(enum.StrEnum)`
- Enum values are lowercase strings: `DRAFT = "draft"`

### Pydantic Schema Patterns

**Schemas:**
- Separate from ORM models
- Located in `schemas/` package
- Use `BaseModel` (not `BaseSettings`)
- Include validation: `Field(min_length=1, max_length=5000)`
- Set `model_config = {"from_attributes": True}` to enable ORM serialization
- Response schemas match database fields exactly (e.g., `PostResponse` includes `created_at`, `updated_at`)
- Separate create/update schemas: `PostCreate`, `PostUpdate`

**Example:**
```python
class PostResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    primary_link: str | None
    image_url: str | None
    scheduled_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    targets: list[PostTargetResponse] = []

    model_config = {"from_attributes": True}
```

## TypeScript Frontend Conventions

### Naming Patterns

**Files:**
- `PascalCase` for component files: `PostsPage.tsx`, `App.tsx`, `AppLayout.tsx`
- `camelCase` for utility/lib files: `auth.ts`, `api.ts`
- `.tsx` extension for React components, `.ts` for plain TypeScript

**Functions:**
- `camelCase` for all functions: `login`, `register`, `getToken`, `isAuthenticated`
- React components are PascalCase (same as file names)

**Variables:**
- `camelCase` for variables: `access_token`, `token_type`, `email`
- Interface/type names `PascalCase`: `AuthResponse`, `User`, `ApiError`

**Types:**
- TypeScript strict mode enabled
- Union syntax: `string | null`, not `Optional<string>`
- Interfaces for public APIs: `interface AuthResponse`, `interface User`
- Generic types: `<T>` for generic API responses

### Code Style

**Formatting:**
- No Prettier config detected; uses TypeScript defaults
- TSConfig `strict: true` enabled
- Linting rules enforced by TypeScript compiler:
  - `noUnusedLocals: true`
  - `noUnusedParameters: true`
  - `noFallthroughCasesInSwitch: true`

**Imports:**
- ES6 module syntax: `import { api } from './api'`
- Relative imports for local files: `import { api } from './api'`
- Path aliases: `@/*` maps to `./src/*` (configured in `tsconfig.app.json`)

### Error Handling

**Patterns:**
- Custom `ApiError` class extending `Error` with `status` property
- Thrown on non-2xx responses
- Fallback error message: `body.detail ?? response.statusText`
- 204 No Content responses return `undefined`

**Example:**
```typescript
if (!response.ok) {
  const body = await response.json().catch(() => ({}));
  throw new ApiError(response.status, body.detail ?? response.statusText);
}
```

### Function Design

**Size:** Functions are concise
- API wrapper functions: 5-15 lines
- Auth helpers: 1-5 lines
- Event handlers/components: varies (PostsPage is 8 lines)

**Parameters:**
- Explicit parameters; no rest parameters in API layer
- Generic type parameters for API methods: `<T>`

**Return Values:**
- Async functions return `Promise<T>`
- Auth functions return `Promise<AuthResponse>` or `string | null` (for getToken)
- Void functions (logout) return nothing

### Module Organization

**Exports:**
- Named exports: `export const api = { ... }`
- Named function exports: `export async function login(...)`
- Default exports: `export default function PostsPage()`

**API Client Pattern:**
- Singleton `api` object with methods: `api.get()`, `api.post()`, `api.put()`, `api.delete()`
- All methods are generic: `<T>(path: string) => request<T>(path, ...)`
- Shared `request()` function handles authorization header and error handling

### React Patterns

**Components:**
- Functional components (no class components)
- Arrow functions or function declarations
- Components are simple and feature-focused (PostsPage shows minimal implementation)

**Layout:**
- `AppLayout.tsx` provides page structure
- Router uses React Router v7

---

*Convention analysis: 2026-03-11*
