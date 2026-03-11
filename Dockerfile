FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

RUN uv sync --no-dev

CMD ["uv", "run", "uvicorn", "smm.main:app", "--host", "0.0.0.0", "--port", "8000"]
