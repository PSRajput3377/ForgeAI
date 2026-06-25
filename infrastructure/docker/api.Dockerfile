# ForgeAI API image. Python pinned to 3.12 (the project target) regardless of
# the host's Python. Uses uv for fast, reproducible installs.
FROM python:3.12-slim

# Install uv (static binary) and git (local clone → commit → push for live GitHub).
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app/apps/api

# Install dependencies first (better layer caching).
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev

# Source is bind-mounted in development (see docker-compose.yml); copy as a
# fallback so the image also runs standalone.
COPY apps/api/ /app/apps/api/
COPY packages/ /app/packages/

ENV PYTHONPATH=/app/apps/api:/app/packages

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
