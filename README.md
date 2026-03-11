# Social Media Manager

A self-hosted social media management app for scheduling and publishing posts to multiple platforms.

## Features

- **Post scheduling** — Create posts targeting multiple social accounts, schedule them for later, or publish immediately
- **Multi-platform publishing** — Facebook and Instagram adapters with a pluggable adapter pattern for adding new platforms
- **Account management** — Connect Facebook accounts via OAuth, view connection status, disconnect accounts
- **Background processing** — APScheduler polls for scheduled posts, Dramatiq workers handle publishing via Redis

## Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x (async), PostgreSQL, Dramatiq + Redis, APScheduler

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, React Router v7

## Getting Started

```bash
# Install Python dependencies
uv sync --dev

# Start infrastructure (Postgres, test Postgres, Redis)
docker compose up db db-test redis -d

# Run database migrations
uv run alembic upgrade head

# Start the API server
uv run uvicorn smm.main:app --reload

# Start the Dramatiq worker (separate terminal)
uv run dramatiq smm.workers.tasks

# Start the React client (separate terminal)
cd src/client && npm install && npm run dev
```

## API Endpoints

| Prefix | Description |
|--------|-------------|
| `/api/v1/auth` | Registration, login, JWT tokens |
| `/api/v1/users` | User profile |
| `/api/v1/social-accounts` | List, delete connected accounts |
| `/api/v1/posts` | Create, update, list, publish posts |
| `/api/v1/oauth/facebook` | Facebook OAuth connect flow |

## Client Pages

| Route | Page |
|-------|------|
| `/` | Dashboard |
| `/posts` | Post management |
| `/accounts` | Connected social accounts |
| `/accounts/facebook/callback` | Facebook OAuth return handler |
