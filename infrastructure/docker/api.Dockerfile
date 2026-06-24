# ForgeAI API image. Python pinned to 3.12 (the project target) regardless of
# the host's Python. Uses uv for fast, reproducible installs.
FROM python:3.12-slim

# Install uv (static binary).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app/apps/api

# Install dependencies first (better layer caching).
COPY apps/api/pyproject.toml ./
RUN uv pip install --system \
    "fastapi>=0.115" "uvicorn[standard]>=0.32" "pydantic>=2.9" \
    "pydantic-settings>=2.6" "sqlalchemy>=2.0" "alembic>=1.14" \
    "psycopg[binary]>=3.2" "redis>=5.2" "loguru>=0.7" "httpx>=0.27"

# Source is bind-mounted in development (see docker-compose.yml); copy as a
# fallback so the image also runs standalone.
COPY apps/api/ /app/apps/api/
COPY packages/ /app/packages/

ENV PYTHONPATH=/app/apps/api:/app/packages

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
