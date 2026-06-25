"""Starter file sets — the actual scaffolds (Phase 13.3).

Each builder returns ``{relative_path: file_contents}``. Pure and deterministic
(no model, no network), so scaffolding is instant and reproducible offline.
"""

from __future__ import annotations


def empty_starter() -> dict[str, str]:
    """A minimal project: just a README, so the dir isn't bare."""
    return {
        "README.md": (
            "# New Project\n\n"
            "Created with ForgeAI. Describe a task in the workspace and the agent "
            "team will extend this project.\n"
        ),
    }


def fastapi_saas_starter() -> dict[str, str]:
    """A non-trivial FastAPI SaaS starter: JWT auth, Postgres, Docker, tests."""
    return {
        "README.md": (
            "# FastAPI SaaS Starter\n\n"
            "A starting point with JWT auth, PostgreSQL, Docker, and tests.\n\n"
            "## Run\n\n"
            "```bash\ndocker compose up --build\n```\n\n"
            "API on http://localhost:8000 — docs at /docs.\n"
        ),
        "requirements.txt": (
            "fastapi>=0.115\n"
            "uvicorn[standard]>=0.32\n"
            "sqlalchemy>=2.0\n"
            "psycopg[binary]>=3.2\n"
            "python-jose[cryptography]>=3.3\n"
            "passlib[bcrypt]>=1.7\n"
            "pydantic-settings>=2.6\n"
            "pytest>=8.3\n"
            "httpx>=0.27\n"
        ),
        "app/__init__.py": "",
        "app/config.py": (
            '"""App settings loaded from the environment."""\n\n'
            "from pydantic_settings import BaseSettings\n\n\n"
            "class Settings(BaseSettings):\n"
            '    database_url: str = "postgresql+psycopg://app:app@db:5432/app"\n'
            '    jwt_secret: str = "change-me"\n'
            '    jwt_algorithm: str = "HS256"\n'
            "    jwt_expire_minutes: int = 1440\n\n\n"
            "settings = Settings()\n"
        ),
        "app/security.py": (
            '"""Password hashing + JWT issue/verify."""\n\n'
            "from datetime import UTC, datetime, timedelta\n\n"
            "from jose import jwt\n"
            "from passlib.context import CryptContext\n\n"
            "from app.config import settings\n\n"
            '_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")\n\n\n'
            "def hash_password(raw: str) -> str:\n"
            "    return _pwd.hash(raw)\n\n\n"
            "def verify_password(raw: str, hashed: str) -> bool:\n"
            "    return _pwd.verify(raw, hashed)\n\n\n"
            "def create_token(sub: str) -> str:\n"
            "    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)\n"
            '    claims = {"sub": sub, "exp": expire}\n'
            "    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)\n"
        ),
        "app/main.py": (
            '"""FastAPI app with register/login (JWT) and a protected route."""\n\n'
            "from fastapi import Depends, FastAPI, HTTPException\n"
            "from fastapi.security import OAuth2PasswordBearer\n"
            "from jose import JWTError, jwt\n"
            "from pydantic import BaseModel\n\n"
            "from app.config import settings\n"
            "from app.security import create_token, hash_password, verify_password\n\n"
            'app = FastAPI(title="SaaS Starter")\n'
            '_oauth = OAuth2PasswordBearer(tokenUrl="login")\n'
            "_users: dict[str, str] = {}  # email -> password_hash (swap for the DB)\n\n\n"
            "class Credentials(BaseModel):\n"
            "    email: str\n"
            "    password: str\n\n\n"
            '@app.get("/health")\n'
            "def health() -> dict:\n"
            '    return {"status": "ok"}\n\n\n'
            '@app.post("/register")\n'
            "def register(body: Credentials) -> dict:\n"
            "    if body.email in _users:\n"
            '        raise HTTPException(409, "already registered")\n'
            "    _users[body.email] = hash_password(body.password)\n"
            '    return {"registered": body.email}\n\n\n'
            '@app.post("/login")\n'
            "def login(body: Credentials) -> dict:\n"
            "    hashed = _users.get(body.email)\n"
            "    if not hashed or not verify_password(body.password, hashed):\n"
            '        raise HTTPException(401, "bad credentials")\n'
            '    return {"access_token": create_token(body.email), "token_type": "bearer"}\n\n\n'
            "def current_user(token: str = Depends(_oauth)) -> str:\n"
            "    try:\n"
            "        claims = jwt.decode(token, settings.jwt_secret, "
            "algorithms=[settings.jwt_algorithm])\n"
            '        return claims["sub"]\n'
            "    except JWTError:\n"
            '        raise HTTPException(401, "invalid token") from None\n\n\n'
            '@app.get("/me")\n'
            "def me(user: str = Depends(current_user)) -> dict:\n"
            '    return {"email": user}\n'
        ),
        "tests/__init__.py": "",
        "tests/test_app.py": (
            '"""Smoke tests for the starter API."""\n\n'
            "from fastapi.testclient import TestClient\n\n"
            "from app.main import app\n\n"
            "client = TestClient(app)\n\n\n"
            "def test_health():\n"
            '    assert client.get("/health").json() == {"status": "ok"}\n\n\n'
            "def test_register_login_and_me():\n"
            '    creds = {"email": "a@x.com", "password": "pw12345"}\n'
            '    assert client.post("/register", json=creds).status_code == 200\n'
            '    token = client.post("/login", json=creds).json()["access_token"]\n'
            '    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})\n'
            '    assert me.json() == {"email": "a@x.com"}\n'
        ),
        "Dockerfile": (
            "FROM python:3.12-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n'
        ),
        "docker-compose.yml": (
            "services:\n"
            "  api:\n"
            "    build: .\n"
            '    ports: ["8000:8000"]\n'
            "    environment:\n"
            "      DATABASE_URL: postgresql+psycopg://app:app@db:5432/app\n"
            "    depends_on: [db]\n"
            "  db:\n"
            "    image: postgres:16-alpine\n"
            "    environment:\n"
            "      POSTGRES_USER: app\n"
            "      POSTGRES_PASSWORD: app\n"
            "      POSTGRES_DB: app\n"
        ),
        ".gitignore": "__pycache__/\n*.pyc\n.env\n.venv/\n",
    }
