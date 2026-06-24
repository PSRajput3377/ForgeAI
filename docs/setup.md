# Setup

How to get ForgeAI running locally.

## Prerequisites

- **Docker** + **Docker Compose** (v2)
- **Node.js** 20+ and **npm** (for the frontend on the host)
- **uv** (for running the backend on the host) — optional if you only use Docker
- ~20 GB free disk for the Ollama models

## 1. Configure environment

```bash
cp .env.example .env       # or: make env
```

The defaults work out of the box for local Docker. Change `JWT_SECRET` before
any non-local use.

## 2. Start the stack

```bash
make up
```

This builds and starts: **postgres, redis, qdrant, ollama, forge-api**.

Check it:

```bash
make ps
curl http://localhost:8000/health      # {"status":"ok",...}
```

| Service    | URL / Port                      |
|------------|---------------------------------|
| API        | http://localhost:8000           |
| API docs   | http://localhost:8000/docs      |
| Postgres   | localhost:5432                  |
| Redis      | localhost:6379                  |
| Qdrant     | http://localhost:6333/dashboard |
| Ollama     | http://localhost:11434          |

## 3. Pull the AI models (once, large download)

```bash
make pull-models
```

Installs `qwen3:8b`, `deepseek-coder`, `llama3.1:8b`, `nomic-embed-text`.

## 4. Run the frontend

```bash
make web-install
make web-dev          # http://localhost:3000
```

The landing page shows a green "API connected" badge when the backend is up.

## Common commands

Run `make help` for the full list. Highlights:

| Command           | Does                                    |
|-------------------|-----------------------------------------|
| `make up`         | Start all services                      |
| `make down`       | Stop all services                       |
| `make logs`       | Tail all logs                           |
| `make clean`      | Stop and **delete all data volumes**    |
| `make pull-models`| Download Ollama models                  |
| `make api-dev`    | Run API on the host with autoreload     |
| `make web-dev`    | Run Next.js dev server                  |
