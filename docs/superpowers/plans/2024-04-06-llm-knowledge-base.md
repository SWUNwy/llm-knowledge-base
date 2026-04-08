# LLM Knowledge Base 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个本地运行的 LLM 知识库应用，支持导入多种来源、自动编译成 Wiki、智能问答。

**Architecture:** FastAPI 后端 + React 前端，数据存储在 Obsidian 兼容的本地文件系统 + SQLite 索引，LiteLLM 提供多模型支持。

**Tech Stack:** Python 3.11+ / FastAPI / SQLite / LiteLLM / React 18 / TypeScript / Vite / TailwindCSS

---

## 文件结构

```
llm-knowledge-base/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # 配置管理
│   │   ├── database.py             # 数据库连接
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # 认证路由
│   │   │   ├── service.py          # 认证逻辑
│   │   │   └── dependencies.py     # 认证中间件
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── document.py         # 文档模型
│   │   │   ├── concept.py          # 概念模型
│   │   │   └── user.py             # 用户模型
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── document_repo.py
│   │   │   └── concept_repo.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py           # 导入服务
│   │   │   ├── compile.py          # 编译服务
│   │   │   └── qa.py               # 问答服务
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # 解析器基类
│   │   │   ├── web.py              # 网页解析
│   │   │   ├── pdf.py              # PDF 解析
│   │   │   ├── video.py            # 视频解析
│   │   │   └── github.py           # GitHub 解析
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── client.py           # LLM 客户端
│   │   │   └── prompts.py          # Prompt 模板
│   │   ├── indexing/
│   │   │   ├── __init__.py
│   │   │   └── indexer.py          # 索引服务
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py
│   │   │   ├── ingest.py
│   │   │   ├── compile.py
│   │   │   ├── qa.py
│   │   │   ├── concepts.py
│   │   │   ├── settings.py
│   │   │   └── system.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── chunker.py          # 文本分块
│   │       └── retry.py            # 重试工具
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             # pytest fixtures
│   │   ├── unit/
│   │   │   ├── test_parsers.py
│   │   │   ├── test_chunker.py
│   │   │   ├── test_llm_client.py
│   │   │   └── test_indexer.py
│   │   ├── integration/
│   │   │   ├── test_auth.py
│   │   │   ├── test_ingest.py
│   │   │   ├── test_compile.py
│   │   │   └── test_qa.py
│   │   └── fixtures/
│   │       ├── pdfs/
│   │       ├── html/
│   │       └── markdown/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── vite-env.d.ts
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Setup.tsx
│   │   │   ├── Import.tsx
│   │   │   ├── Library.tsx
│   │   │   ├── Chat.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useApi.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── tsconfig.json
│
├── docs/
│   ├── api.yaml
│   └── design.md
│
├── requirements/
│   └── active/R001-llm-knowledge-base/
│
├── scripts/
│   ├── setup.sh
│   ├── dev.sh
│   └── test.sh
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Phase 1: 项目初始化

### Task 1.1: 创建后端项目结构

**Files:**
- Create: `backend/src/__init__.py`
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `backend/pyproject.toml`

- [ ] **Step 1: 创建后端目录结构**

```bash
mkdir -p backend/src/{auth,models,repositories,services,parsers,llm,indexing,routers,utils}
mkdir -p backend/tests/{unit,integration,fixtures/{pdfs,html,markdown}}
touch backend/src/__init__.py
touch backend/src/{auth,models,repositories,services,parsers,llm,indexing,routers,utils}/__init__.py
```

- [ ] **Step 2: 创建 requirements.txt**

```text
# Web 框架
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6

# 数据库
aiosqlite>=0.19.0

# LLM
litellm>=1.20.0

# 解析器
beautifulsoup4>=4.12.0
readability-lxml>=0.8.1
httpx>=0.26.0
PyMuPDF>=1.23.0
youtube-transcript-api>=0.6.0
GitPython>=3.1.0

# 工具
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
aiofiles>=23.2.0
```

- [ ] **Step 3: 创建 requirements-dev.txt**

```text
-r requirements.txt

# 测试
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
vcrpy>=6.0.0
httpx>=0.26.0

# 代码质量
ruff>=0.1.0
mypy>=1.8.0

# 类型存根
types-aiofiles>=23.2.0
```

- [ ] **Step 4: 创建 pyproject.toml**

```toml
[project]
name = "llm-knowledge-base"
version = "0.1.0"
description = "LLM-powered knowledge base"
requires-python = ">=3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=src --cov-report=term-missing"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

- [ ] **Step 5: 提交**

```bash
git add backend/
git commit -m "chore: init backend project structure"
```

---

### Task 1.2: 创建配置模块

**Files:**
- Create: `backend/src/config.py`

- [ ] **Step 1: 创建配置类**

```python
# backend/src/config.py
"""应用配置管理"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_port: int = 8000

    # Vault 配置
    vault_path: str

    # LLM 配置
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None
    llm_default_model: str = "gemini/gemini-pro"

    # Embedding 配置
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # 编译配置
    auto_compile: bool = True
    compile_batch_size: int = 5

    # 并发配置
    max_concurrent_tasks: int = 3

    # 日志配置
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/config.py
git commit -m "feat: add configuration module"
```

---

### Task 1.3: 创建数据库模块

**Files:**
- Create: `backend/src/database.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: 写数据库测试**

```python
# backend/tests/conftest.py
"""pytest 配置和 fixtures"""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

from src.database import Database


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_vault() -> Generator[Path, None, None]:
    """创建临时 vault 目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir)
        (vault_path / ".wiki").mkdir()
        (vault_path / "raw" / "web").mkdir(parents=True)
        (vault_path / "raw" / "papers").mkdir(parents=True)
        (vault_path / "raw" / "videos").mkdir(parents=True)
        (vault_path / "raw" / "code").mkdir(parents=True)
        (vault_path / "wiki" / "concepts").mkdir(parents=True)
        (vault_path / "wiki" / "sources").mkdir(parents=True)
        (vault_path / "outputs" / "answers").mkdir(parents=True)
        yield vault_path


@pytest_asyncio.fixture
async def db(temp_vault: Path) -> AsyncGenerator[Database, None]:
    """创建测试数据库"""
    database = Database(temp_vault / ".wiki" / "metadata.db")
    await database.init()
    yield database
    await database.close()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/conftest.py -v
```

Expected: FAIL - `Database` not defined

- [ ] **Step 3: 创建数据库模块**

```python
# backend/src/database.py
"""数据库连接和初始化"""

import json
from pathlib import Path

import aiosqlite


class Database:
    """SQLite 数据库管理"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def init(self) -> None:
        """初始化数据库连接和表结构"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _create_tables(self) -> None:
        """创建数据库表"""
        await self._conn.executescript("""
            -- 用户表
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 文档表
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                path TEXT NOT NULL,
                title TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}'
            );

            -- 全文搜索虚拟表
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                id, title, content,
                content='documents',
                tokenize='unicode61'
            );

            -- 概念表
            CREATE TABLE IF NOT EXISTS concepts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                wiki_path TEXT,
                mention_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 文档-概念关联
            CREATE TABLE IF NOT EXISTS doc_concepts (
                doc_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                relevance_score REAL DEFAULT 0.0,
                PRIMARY KEY (doc_id, concept_id),
                FOREIGN KEY (doc_id) REFERENCES documents(id),
                FOREIGN KEY (concept_id) REFERENCES concepts(id)
            );

            -- 链接关系
            CREATE TABLE IF NOT EXISTS links (
                from_path TEXT NOT NULL,
                to_path TEXT NOT NULL,
                link_type TEXT DEFAULT 'explicit',
                confidence REAL DEFAULT 1.0,
                PRIMARY KEY (from_path, to_path)
            );

            -- 编译任务
            CREATE TABLE IF NOT EXISTS compile_tasks (
                id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'pending',
                total_docs INTEGER DEFAULT 0,
                completed_docs INTEGER DEFAULT 0,
                failed_docs INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                result TEXT
            );

            -- 问答历史
            CREATE TABLE IF NOT EXISTS qa_history (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT,
                sources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 索引
            CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
            CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
            CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name);
        """)
        await self._conn.commit()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not initialized")
        return self._conn
```

- [ ] **Step 4: 添加 conftest 导入并运行测试**

```python
# backend/tests/conftest.py 顶部添加
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

```bash
cd backend && python -m pytest tests/conftest.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/database.py backend/tests/conftest.py
git commit -m "feat: add database module with schema"
```

---

### Task 1.4: 创建 FastAPI 主入口

**Files:**
- Create: `backend/src/main.py`
- Create: `backend/tests/integration/test_main.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/integration/test_main.py
"""主应用测试"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_openapi_endpoint(client: TestClient):
    """测试 OpenAPI 规范端点"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "LLM Knowledge Base API"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/integration/test_main.py -v
```

Expected: FAIL - `client` fixture not defined

- [ ] **Step 3: 添加测试 fixture**

```python
# backend/tests/conftest.py 添加

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(temp_vault: Path, monkeypatch) -> TestClient:
    """创建测试客户端"""
    monkeypatch.setenv("VAULT_PATH", str(temp_vault))
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key")

    from src.main import app

    return TestClient(app)
```

- [ ] **Step 4: 创建主应用**

```python
# backend/src/main.py
"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.database import Database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """应用生命周期管理"""
    settings = get_settings()
    vault_path = Path(settings.vault_path)

    # 初始化目录结构
    for subdir in [
        ".wiki",
        "raw/web",
        "raw/papers",
        "raw/videos",
        "raw/code",
        "wiki/concepts",
        "wiki/sources",
        "outputs/answers",
    ]:
        (vault_path / subdir).mkdir(parents=True, exist_ok=True)

    # 初始化数据库
    db = Database(vault_path / ".wiki" / "metadata.db")
    await db.init()
    app.state.db = db

    yield

    # 清理
    await db.close()


app = FastAPI(
    title="LLM Knowledge Base API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}
```

- [ ] **Step 5: 运行测试**

```bash
cd backend && python -m pytest tests/integration/test_main.py -v
```

Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/src/main.py backend/tests/integration/test_main.py
git commit -m "feat: add FastAPI main entry point"
```

---

## Phase 2: 认证模块

### Task 2.1: 用户模型和密码工具

**Files:**
- Create: `backend/src/models/user.py`
- Create: `backend/src/auth/password.py`
- Create: `backend/tests/unit/test_password.py`

- [ ] **Step 1: 写密码测试**

```python
# backend/tests/unit/test_password.py
"""密码工具测试"""

import pytest

from src.auth.password import verify_password, hash_password


def test_hash_password():
    """测试密码哈希"""
    password = "test-password-123"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    """测试正确密码验证"""
    password = "test-password-123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """测试错误密码验证"""
    password = "test-password-123"
    wrong_password = "wrong-password"
    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/unit/test_password.py -v
```

Expected: FAIL - module not found

- [ ] **Step 3: 创建密码工具**

```python
# backend/src/auth/password.py
"""密码哈希和验证"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)
```

- [ ] **Step 4: 创建用户模型**

```python
# backend/src/models/user.py
"""用户模型"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel


class User(BaseModel):
    """用户"""

    id: str
    username: str
    password_hash: str
    created_at: datetime


class UserCreate(BaseModel):
    """创建用户请求"""

    username: str
    password: str


class UserLogin(BaseModel):
    """登录请求"""

    username: str
    password: str


class Token(BaseModel):
    """Token 响应"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


def create_user_id() -> str:
    """生成用户 ID"""
    return f"user-{uuid4().hex[:12]}"
```

- [ ] **Step 5: 运行测试**

```bash
cd backend && python -m pytest tests/unit/test_password.py -v
```

Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/src/auth/password.py backend/src/models/user.py backend/tests/unit/test_password.py
git commit -m "feat: add password utilities and user models"
```

---

### Task 2.2: JWT Token 工具

**Files:**
- Create: `backend/src/auth/jwt.py`
- Create: `backend/tests/unit/test_jwt.py`

- [ ] **Step 1: 写 JWT 测试**

```python
# backend/tests/unit/test_jwt.py
"""JWT 工具测试"""

from datetime import timedelta

import pytest

from src.auth.jwt import create_token, decode_token


def test_create_and_decode_token():
    """测试创建和解码 token"""
    data = {"sub": "user-123", "username": "admin"}
    token = create_token(data)
    payload = decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["username"] == "admin"


def test_token_contains_exp():
    """测试 token 包含过期时间"""
    data = {"sub": "user-123"}
    token = create_token(data)
    payload = decode_token(token)

    assert "exp" in payload
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/unit/test_jwt.py -v
```

Expected: FAIL - module not found

- [ ] **Step 3: 创建 JWT 工具**

```python
# backend/src/auth/jwt.py
"""JWT Token 工具"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from src.config import get_settings


def create_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """创建 JWT token"""
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)

    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, settings.app_secret_key, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """解码 JWT token"""
    settings = get_settings()
    payload = jwt.decode(token, settings.app_secret_key, algorithms=["HS256"])
    return payload


def verify_token(token: str) -> dict[str, Any] | None:
    """验证 token，返回 payload 或 None"""
    try:
        return decode_token(token)
    except JWTError:
        return None
```

- [ ] **Step 4: 运行测试**

```bash
cd backend && python -m pytest tests/unit/test_jwt.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/auth/jwt.py backend/tests/unit/test_jwt.py
git commit -m "feat: add JWT token utilities"
```

---

### Task 2.3: 认证服务和路由

**Files:**
- Create: `backend/src/auth/service.py`
- Create: `backend/src/auth/dependencies.py`
- Create: `backend/src/auth/router.py`
- Create: `backend/tests/integration/test_auth.py`

- [ ] **Step 1: 写认证集成测试**

```python
# backend/tests/integration/test_auth.py
"""认证 API 集成测试"""

import pytest
from fastapi.testclient import TestClient


def test_setup_account(client: TestClient):
    """测试首次设置账户"""
    response = client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "test-password-123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_setup_account_already_exists(client: TestClient):
    """测试重复设置账户"""
    # 首次设置
    client.post("/api/v1/auth/setup", json={"username": "admin", "password": "test-password-123"})

    # 重复设置
    response = client.post(
        "/api/v1/auth/setup",
        json={"username": "another", "password": "test-password-456"},
    )
    assert response.status_code == 400
    assert "already" in response.json()["error"]["message"].lower()


def test_login_success(client: TestClient):
    """测试登录成功"""
    # 先设置账户
    client.post("/api/v1/auth/setup", json={"username": "admin", "password": "test-password-123"})

    # 登录
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "test-password-123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["token"].startswith("ey")  # JWT starts with ey


def test_login_wrong_password(client: TestClient):
    """测试密码错误"""
    client.post("/api/v1/auth/setup", json={"username": "admin", "password": "test-password-123"})

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_protected_endpoint_without_token(client: TestClient):
    """测试无 token 访问受保护端点"""
    response = client.get("/api/v1/documents")
    assert response.status_code == 401


def test_protected_endpoint_with_token(client: TestClient):
    """测试有 token 访问受保护端点"""
    # 设置并登录
    client.post("/api/v1/auth/setup", json={"username": "admin", "password": "test-password-123"})
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "test-password-123"},
    )
    token = login_resp.json()["token"]

    # 访问受保护端点
    response = client.get(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/integration/test_auth.py -v
```

Expected: FAIL - 404 (route not found)

- [ ] **Step 3: 创建认证服务**

```python
# backend/src/auth/service.py
"""认证服务"""

import aiosqlite

from src.auth.password import hash_password, verify_password
from src.auth.jwt import create_token
from src.models.user import User, UserCreate, UserLogin, Token, create_user_id


class AuthService:
    """认证服务"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def is_setup_complete(self) -> bool:
        """检查是否已完成初始化"""
        cursor = await self.db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] > 0

    async def setup(self, user_create: UserCreate) -> User:
        """初始化账户"""
        if await self.is_setup_complete():
            raise ValueError("Account already set up")

        user = User(
            id=create_user_id(),
            username=user_create.username,
            password_hash=hash_password(user_create.password),
            created_at=datetime.now(timezone.utc),
        )

        await self.db.execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user.id, user.username, user.password_hash, user.created_at.isoformat()),
        )
        await self.db.commit()

        return user

    async def login(self, user_login: UserLogin) -> Token:
        """登录"""
        cursor = await self.db.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
            (user_login.username,),
        )
        row = await cursor.fetchone()

        if not row:
            raise ValueError("Invalid credentials")

        if not verify_password(user_login.password, row["password_hash"]):
            raise ValueError("Invalid credentials")

        token = create_token({"sub": row["id"], "username": row["username"]})

        return Token(access_token=token)

    async def get_user_by_id(self, user_id: str) -> User | None:
        """通过 ID 获取用户"""
        cursor = await self.db.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
```

需要添加导入:

```python
# backend/src/auth/service.py 顶部
from datetime import datetime, timezone
```

- [ ] **Step 4: 创建认证依赖**

```python
# backend/src/auth/dependencies.py
"""认证依赖"""

from typing import Annotated

import aiosqlite
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.jwt import verify_token
from src.auth.service import AuthService
from src.database import Database
from src.main import app
from src.models.user import User

security = HTTPBearer()


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接"""
    return app.state.db


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[aiosqlite.Connection, Depends(get_db)],
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
```

- [ ] **Step 5: 创建认证路由**

```python
# backend/src/auth/router.py
"""认证路由"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.auth.dependencies import get_current_user, get_db
from src.auth.service import AuthService
from src.models.user import User, UserCreate, UserLogin, Token

router = APIRouter(prefix="/auth", tags=["Auth"])


class SuccessResponse(BaseModel):
    success: bool
    message: str = ""


class ErrorResponse(BaseModel):
    error: dict


@router.post("/setup", response_model=SuccessResponse)
async def setup(
    user_create: UserCreate,
    db=Depends(get_db),
):
    """初始化账户"""
    auth_service = AuthService(db)

    try:
        await auth_service.setup(user_create)
        return SuccessResponse(success=True, message="Account created successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "ALREADY_SETUP", "message": str(e)}},
        )


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db=Depends(get_db),
):
    """登录"""
    auth_service = AuthService(db)

    try:
        return await auth_service.login(user_login)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid credentials"}},
        )


@router.post("/logout")
async def logout(current_user: Annotated[User, Depends(get_current_user)]):
    """登出"""
    # JWT 无状态，客户端删除 token 即可
    return {"success": True}
```

- [ ] **Step 6: 注册路由到主应用**

```python
# backend/src/main.py 添加导入和注册

from src.auth.router import router as auth_router

# ... 在 app 创建后添加 ...
app.include_router(auth_router, prefix="/api/v1")
```

- [ ] **Step 7: 运行测试**

```bash
cd backend && python -m pytest tests/integration/test_auth.py -v
```

Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add backend/src/auth/ backend/tests/integration/test_auth.py backend/src/main.py
git commit -m "feat: add authentication service and routes"
```

---

## Phase 3: 文档模型和数据层

### Task 3.1: 文档模型

**Files:**
- Create: `backend/src/models/document.py`
- Create: `backend/tests/unit/test_document_model.py`

- [ ] **Step 1: 写文档模型测试**

```python
# backend/tests/unit/test_document_model.py
"""文档模型测试"""

from src.models.document import Document, DocumentCreate, DocumentType


def test_document_create_defaults():
    """测试文档创建默认值"""
    doc = DocumentCreate(
        type=DocumentType.WEB,
        title="Test Document",
        content="Test content",
    )

    assert doc.status == "pending"
    assert doc.tags == []
    assert doc.metadata == {}


def test_document_to_markdown():
    """测试文档转 Markdown"""
    doc = Document(
        id="doc-123",
        type=DocumentType.WEB,
        path="raw/web/doc-123.md",
        title="Test Document",
        content="This is the content.",
        source_url="https://example.com",
        status="pending",
        tags=["test", "example"],
    )

    md = doc.to_markdown()

    assert "id: doc-123" in md
    assert "title: Test Document" in md
    assert "https://example.com" in md
    assert "This is the content." in md
```

- [ ] **Step 2: 创建文档模型**

```python
# backend/src/models/document.py
"""文档模型"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """文档类型"""

    WEB = "web"
    PAPER = "paper"
    VIDEO = "video"
    CODE = "code"


class DocumentStatus(str, Enum):
    """文档状态"""

    PENDING = "pending"
    PROCESSED = "processed"


class DocumentBase(BaseModel):
    """文档基础模型"""

    type: DocumentType
    title: str
    content: str
    source_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    """创建文档请求"""

    status: str = "pending"


class Document(DocumentBase):
    """完整文档"""

    id: str
    path: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        frontmatter = [
            f"id: {self.id}",
            f"type: {self.type.value}",
        ]
        if self.source_url:
            frontmatter.append(f"source: {self.source_url}")
        frontmatter.append(f"title: {self.title}")
        frontmatter.append(f"created: {self.created_at.date().isoformat()}")
        frontmatter.append(f"tags: {self.tags}")
        frontmatter.append(f"status: {self.status}")

        return f"""---
{chr(10).join(frontmatter)}
---

# {self.title}

{self.content}
"""

    @classmethod
    def create_id(cls) -> str:
        """生成文档 ID"""
        return f"doc-{uuid4().hex[:12]}"


class DocumentSummary(BaseModel):
    """文档摘要（列表显示用）"""

    id: str
    title: str
    type: DocumentType
    status: str
    created_at: datetime
    tags: list[str]


class DocumentListResponse(BaseModel):
    """文档列表响应"""

    total: int
    page: int
    limit: int
    items: list[DocumentSummary]


class SearchResult(BaseModel):
    """搜索结果"""

    id: str
    title: str
    snippet: str
    score: float
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/unit/test_document_model.py -v
```

Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add backend/src/models/document.py backend/tests/unit/test_document_model.py
git commit -m "feat: add document models"
```

---

### Task 3.2: 文档 Repository

**Files:**
- Create: `backend/src/repositories/document_repo.py`
- Create: `backend/tests/unit/test_document_repo.py`

- [ ] **Step 1: 写 Repository 测试**

```python
# backend/tests/unit/test_document_repo.py
"""文档 Repository 测试"""

import pytest
from datetime import datetime

from src.models.document import Document, DocumentType, DocumentCreate
from src.repositories.document_repo import DocumentRepository


@pytest.mark.asyncio
async def test_create_document(db):
    """测试创建文档"""
    repo = DocumentRepository(db)

    doc_create = DocumentCreate(
        type=DocumentType.WEB,
        title="Test Article",
        content="This is test content.",
        source_url="https://example.com/test",
        tags=["test"],
    )

    doc = await repo.create(doc_create, path="raw/web/test.md")

    assert doc.id.startswith("doc-")
    assert doc.title == "Test Article"
    assert doc.status == "pending"


@pytest.mark.asyncio
async def test_get_by_id(db):
    """测试通过 ID 获取文档"""
    repo = DocumentRepository(db)

    # 先创建
    doc_create = DocumentCreate(
        type=DocumentType.WEB,
        title="Test",
        content="Content",
    )
    created = await repo.create(doc_create, path="raw/web/test.md")

    # 再获取
    found = await repo.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
async def test_list_documents(db):
    """测试列出文档"""
    repo = DocumentRepository(db)

    # 创建多个文档
    for i in range(5):
        await repo.create(
            DocumentCreate(
                type=DocumentType.WEB,
                title=f"Document {i}",
                content=f"Content {i}",
            ),
            path=f"raw/web/doc{i}.md",
        )

    # 列出
    result = await repo.list(limit=3, offset=0)

    assert result.total == 5
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_update_status(db):
    """测试更新状态"""
    repo = DocumentRepository(db)

    doc = await repo.create(
        DocumentCreate(type=DocumentType.WEB, title="Test", content="Content"),
        path="raw/web/test.md",
    )

    await repo.update_status(doc.id, "processed")

    updated = await repo.get_by_id(doc.id)
    assert updated.status == "processed"
```

- [ ] **Step 2: 创建 Repository**

```python
# backend/src/repositories/document_repo.py
"""文档 Repository"""

import json
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from src.models.document import (
    Document,
    DocumentCreate,
    DocumentSummary,
    DocumentListResponse,
    DocumentType,
)


class DocumentRepository:
    """文档数据访问"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, doc_create: DocumentCreate, path: str) -> Document:
        """创建文档"""
        doc_id = Document.create_id()
        now = datetime.now(timezone.utc)

        await self.db.execute(
            """
            INSERT INTO documents (id, type, path, title, status, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                doc_create.type.value,
                path,
                doc_create.title,
                doc_create.status,
                now.isoformat(),
                now.isoformat(),
                json.dumps({"tags": doc_create.tags, "source_url": doc_create.source_url}),
            ),
        )

        await self.db.execute(
            "INSERT INTO documents_fts (id, title, content) VALUES (?, ?, ?)",
            (doc_id, doc_create.title, doc_create.content),
        )

        await self.db.commit()

        return Document(
            id=doc_id,
            type=doc_create.type,
            path=path,
            title=doc_create.title,
            content=doc_create.content,
            source_url=doc_create.source_url,
            status=doc_create.status,
            tags=doc_create.tags,
            metadata=doc_create.metadata,
            created_at=now,
            updated_at=now,
        )

    async def get_by_id(self, doc_id: str) -> Optional[Document]:
        """通过 ID 获取文档"""
        cursor = await self.db.execute(
            "SELECT * FROM documents WHERE id = ?",
            (doc_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_document(row)

    async def list(
        self,
        type: Optional[DocumentType] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> DocumentListResponse:
        """列出文档"""

        # 构建查询
        conditions = []
        params = []

        if type:
            conditions.append("type = ?")
            params.append(type.value)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 获取总数
        count_cursor = await self.db.execute(
            f"SELECT COUNT(*) FROM documents WHERE {where_clause}",
            params,
        )
        total = (await count_cursor.fetchone())[0]

        # 获取数据
        data_cursor = await self.db.execute(
            f"""
            SELECT id, type, path, title, status, created_at, metadata
            FROM documents
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )
        rows = await data_cursor.fetchall()

        items = [
            DocumentSummary(
                id=row["id"],
                title=row["title"],
                type=DocumentType(row["type"]),
                status=row["status"],
                created_at=datetime.fromisoformat(row["created_at"]),
                tags=json.loads(row["metadata"]).get("tags", []),
            )
            for row in rows
        ]

        return DocumentListResponse(
            total=total,
            page=offset // limit + 1,
            limit=limit,
            items=items,
        )

    async def update_status(self, doc_id: str, status: str) -> None:
        """更新文档状态"""
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE documents SET status = ?, updated_at = ? WHERE id = ?",
            (status, now.isoformat(), doc_id),
        )
        await self.db.commit()

    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        await self.db.execute("DELETE FROM documents_fts WHERE id = ?", (doc_id,))
        cursor = await self.db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await self.db.commit()
        return cursor.rowcount > 0

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """全文搜索"""
        cursor = await self.db.execute(
            """
            SELECT d.id, d.title, d.type, d.status, fts.content
            FROM documents_fts fts
            JOIN documents d ON fts.id = d.id
            WHERE documents_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        )
        rows = await cursor.fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "type": row["type"],
                "status": row["status"],
                "snippet": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
            }
            for row in rows
        ]

    def _row_to_document(self, row: aiosqlite.Row) -> Document:
        """将数据库行转换为文档对象"""
        metadata = json.loads(row["metadata"])
        return Document(
            id=row["id"],
            type=DocumentType(row["type"]),
            path=row["path"],
            title=row["title"],
            content="",  # 内容需要单独从文件读取
            source_url=metadata.get("source_url"),
            status=row["status"],
            tags=metadata.get("tags", []),
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/unit/test_document_repo.py -v
```

Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add backend/src/repositories/document_repo.py backend/tests/unit/test_document_repo.py
git commit -m "feat: add document repository"
```

---

## Phase 4: 导入模块

### Task 4.1: 解析器基类和网页解析器

**Files:**
- Create: `backend/src/parsers/base.py`
- Create: `backend/src/parsers/web.py`
- Create: `backend/tests/fixtures/html/simple.html`
- Create: `backend/tests/unit/test_web_parser.py`

- [ ] **Step 1: 创建测试 fixture**

```html
<!-- backend/tests/fixtures/html/simple.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Test Article</title>
    <meta name="author" content="Test Author">
</head>
<body>
    <article>
        <h1>Test Article Title</h1>
        <p>This is the first paragraph of the test article.</p>
        <p>This is the second paragraph with more content.</p>
    </article>
</body>
</html>
```

- [ ] **Step 2: 写解析器测试**

```python
# backend/tests/unit/test_web_parser.py
"""网页解析器测试"""

from pathlib import Path

import pytest

from src.parsers.web import WebParser
from src.parsers.base import ParseResult


@pytest.fixture
def web_parser():
    return WebParser()


@pytest.mark.asyncio
async def test_parse_local_html(web_parser):
    """测试解析本地 HTML"""
    html_path = Path(__file__).parent.parent / "fixtures" / "html" / "simple.html"

    result = await web_parser.parse_file(html_path)

    assert result.success is True
    assert "Test Article" in result.title
    assert "first paragraph" in result.content
    assert result.metadata.get("author") == "Test Author"
```

- [ ] **Step 3: 创建解析器基类**

```python
# backend/src/parsers/base.py
"""解析器基类"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any


@dataclass
class ParseResult:
    """解析结果"""

    success: bool
    title: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    images: list[str] = field(default_factory=list)
    error: Optional[str] = None


class BaseParser:
    """解析器基类"""

    async def parse_url(self, url: str) -> ParseResult:
        """从 URL 解析"""
        raise NotImplementedError

    async def parse_file(self, path: Path) -> ParseResult:
        """从文件解析"""
        raise NotImplementedError
```

- [ ] **Step 4: 创建网页解析器**

```python
# backend/src/parsers/web.py
"""网页解析器"""

from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from readability.readability import Document

from src.parsers.base import BaseParser, ParseResult


class WebParser(BaseParser):
    """网页解析器"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    async def parse_url(self, url: str) -> ParseResult:
        """从 URL 解析网页"""
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            return self._parse_html(response.text, url)

        except httpx.HTTPError as e:
            return ParseResult(
                success=False,
                error=f"HTTP error: {e}",
            )
        except Exception as e:
            return ParseResult(
                success=False,
                error=f"Parse error: {e}",
            )

    async def parse_file(self, path: Path) -> ParseResult:
        """从本地 HTML 文件解析"""
        try:
            content = path.read_text(encoding="utf-8")
            return self._parse_html(content, f"file://{path}")
        except Exception as e:
            return ParseResult(
                success=False,
                error=f"File read error: {e}",
            )

    def _parse_html(self, html: str, source_url: str) -> ParseResult:
        """解析 HTML 内容"""
        # 使用 readability 提取正文
        doc = Document(html)
        title = doc.title()
        summary = doc.summary()

        # 使用 BeautifulSoup 清理
        soup = BeautifulSoup(summary, "html.parser")

        # 提取文本
        text = soup.get_text(separator="\n", strip=True)

        # 提取元数据
        metadata = {}
        full_soup = BeautifulSoup(html, "html.parser")

        if meta_author := full_soup.find("meta", attrs={"name": "author"}):
            metadata["author"] = meta_author.get("content", "")

        if meta_desc := full_soup.find("meta", attrs={"name": "description"}):
            metadata["description"] = meta_desc.get("content", "")

        metadata["source_url"] = source_url

        return ParseResult(
            success=True,
            title=title,
            content=text,
            metadata=metadata,
        )
```

- [ ] **Step 5: 运行测试**

```bash
cd backend && python -m pytest tests/unit/test_web_parser.py -v
```

Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/src/parsers/ backend/tests/fixtures/ backend/tests/unit/test_web_parser.py
git commit -m "feat: add web parser"
```

---

由于计划篇幅较长，我将继续创建完整的计划文档...

---

## 后续任务概要

以下是剩余任务的简要概述，完整实施时需要按相同格式展开：

### Phase 4 续: 导入模块 (续)
- Task 4.2: PDF 解析器
- Task 4.3: 视频解析器
- Task 4.4: GitHub 解析器
- Task 4.5: 导入服务和路由

### Phase 5: LLM 集成
- Task 5.1: LLM Client (LiteLLM 封装)
- Task 5.2: Prompt 模板
- Task 5.3: 重试和错误处理

### Phase 6: 编译模块
- Task 6.1: 文本分块器
- Task 6.2: 编译服务
- Task 6.3: 概念提取
- Task 6.4: 编译路由

### Phase 7: 问答模块
- Task 7.1: 索引服务
- Task 7.2: 问答服务
- Task 7.3: 流式输出 (SSE)
- Task 7.4: 问答路由

### Phase 8: 前端开发
- Task 8.1: 创建 React 项目
- Task 8.2: 路由和布局
- Task 8.3: 登录/设置页面
- Task 8.4: 导入页面
- Task 8.5: 文库页面
- Task 8.6: 问答页面

### Phase 9: 集成和部署
- Task 9.1: E2E 测试
- Task 9.2: 性能测试
- Task 9.3: 文档完善

---

## 质量检查清单

实施完成后需要验证：

- [ ] 所有单元测试通过 (`pytest tests/unit -v`)
- [ ] 所有集成测试通过 (`pytest tests/integration -v`)
- [ ] 代码覆盖率 ≥ 80% (`pytest --cov --cov-fail-under=80`)
- [ ] 无硬编码配置（所有配置通过环境变量）
- [ ] 无非测试文件中的 Mock 数据
- [ ] LLM 测试使用 VCR 录制
- [ ] 前端构建成功 (`npm run build`)
- [ ] 前端测试通过 (`npm run test`)

---

### Task 4.2: PDF 解析器

**Files:**
- Create: `backend/src/parsers/pdf.py`
- Create: `backend/tests/fixtures/pdfs/simple.pdf` (手动创建或使用脚本)
- Create: `backend/tests/unit/test_pdf_parser.py`

- [ ] **Step 1: 写 PDF 解析器测试**

```python
# backend/tests/unit/test_pdf_parser.py
"""PDF 解析器测试"""

from pathlib import Path

import pytest

from src.parsers.pdf import PDFParser
from src.parsers.base import ParseResult


@pytest.fixture
def pdf_parser():
    return PDFParser()


@pytest.mark.asyncio
async def test_parse_pdf_file_not_found(pdf_parser):
    """测试文件不存在"""
    result = await pdf_parser.parse_file(Path("/nonexistent/file.pdf"))
    
    assert result.success is False
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_parse_pdf_invalid_format(pdf_parser, tmp_path):
    """测试非法格式"""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not a pdf")
    
    result = await pdf_parser.parse_file(txt_file)
    
    assert result.success is False
    assert "unsupported" in result.error.lower() or "invalid" in result.error.lower()
```

- [ ] **Step 2: 创建 PDF 解析器**

```python
# backend/src/parsers/pdf.py
"""PDF 解析器"""

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from src.parsers.base import BaseParser, ParseResult


class PDFParser(BaseParser):
    """PDF 解析器"""

    async def parse_url(self, url: str) -> ParseResult:
        """PDF 不支持 URL 解析"""
        return ParseResult(
            success=False,
            error="PDF parser does not support URL parsing",
        )

    async def parse_file(self, path: Path) -> ParseResult:
        """解析 PDF 文件"""
        if not path.exists():
            return ParseResult(
                success=False,
                error=f"File not found: {path}",
            )

        if path.suffix.lower() != ".pdf":
            return ParseResult(
                success=False,
                error=f"Unsupported format: {path.suffix}",
            )

        try:
            doc = fitz.open(path)
            
            # 提取文本
            text_parts = []
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"## Page {page_num + 1}\n\n{text}")
            
            content = "\n\n".join(text_parts)
            
            # 提取元数据
            metadata: dict[str, Any] = {
                "page_count": doc.page_count,
                "source_path": str(path),
            }
            
            if doc.metadata:
                if title := doc.metadata.get("title"):
                    metadata["title"] = title
                if author := doc.metadata.get("author"):
                    metadata["author"] = author
                if created := doc.metadata.get("creationDate"):
                    metadata["created_date"] = created
            
            title = metadata.get("title") or path.stem
            
            doc.close()
            
            return ParseResult(
                success=True,
                title=title,
                content=content,
                metadata=metadata,
            )
            
        except Exception as e:
            return ParseResult(
                success=False,
                error=f"PDF parse error: {e}",
            )
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/unit/test_pdf_parser.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/parsers/pdf.py backend/tests/unit/test_pdf_parser.py
git commit -m "feat: add PDF parser"
```

---

### Task 4.3: 导入服务

**Files:**
- Create: `backend/src/services/ingest.py`
- Create: `backend/src/routers/ingest.py`
- Create: `backend/tests/integration/test_ingest.py`

- [ ] **Step 1: 写导入集成测试**

```python
# backend/tests/integration/test_ingest.py
"""导入 API 集成测试"""

import pytest
from fastapi.testclient import TestClient


def test_ingest_url(client: TestClient, auth_headers: dict):
    """测试 URL 导入"""
    response = client.post(
        "/api/v1/ingest/url",
        json={"url": "https://example.com", "tags": ["test"]},
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] in ["pending", "processing"]


def test_ingest_file_not_found(client: TestClient, auth_headers: dict):
    """测试导入不存在的文件"""
    response = client.post(
        "/api/v1/ingest/file",
        json={"path": "/nonexistent/file.pdf", "tags": []},
        headers=auth_headers,
    )
    
    assert response.status_code == 404


def test_ingest_requires_auth(client: TestClient):
    """测试导入需要认证"""
    response = client.post(
        "/api/v1/ingest/url",
        json={"url": "https://example.com"},
    )
    
    assert response.status_code == 401
```

- [ ] **Step 2: 创建导入服务**

```python
# backend/src/services/ingest.py
"""导入服务"""

from pathlib import Path
from typing import Optional
from uuid import uuid4

from src.parsers.web import WebParser
from src.parsers.pdf import PDFParser
from src.parsers.base import ParseResult
from src.models.document import DocumentCreate, DocumentType
from src.repositories.document_repo import DocumentRepository


class IngestService:
    """导入服务"""

    def __init__(self, vault_path: Path, doc_repo: DocumentRepository):
        self.vault_path = vault_path
        self.doc_repo = doc_repo
        self.web_parser = WebParser()
        self.pdf_parser = PDFParser()

    async def ingest_url(
        self,
        url: str,
        tags: Optional[list[str]] = None,
    ) -> dict:
        """导入 URL"""
        tags = tags or []
        
        # 解析 URL
        result = await self.web_parser.parse_url(url)
        
        if not result.success:
            raise ValueError(f"Failed to parse URL: {result.error}")
        
        # 保存文档
        doc_id = self._generate_id()
        doc_path = self.vault_path / "raw" / "web" / f"{doc_id}.md"
        
        # 创建 markdown 文件
        content = self._create_raw_markdown(
            id=doc_id,
            type=DocumentType.WEB,
            title=result.title,
            content=result.content,
            source_url=url,
            tags=tags,
            metadata=result.metadata,
        )
        
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(content, encoding="utf-8")
        
        # 创建数据库记录
        doc_create = DocumentCreate(
            type=DocumentType.WEB,
            title=result.title,
            content=result.content,
            source_url=url,
            tags=tags,
            metadata=result.metadata,
            status="pending",
        )
        
        doc = await self.doc_repo.create(doc_create, str(doc_path.relative_to(self.vault_path)))
        
        return {
            "id": doc.id,
            "status": doc.status,
            "title": doc.title,
            "type": doc.type.value,
        }

    async def ingest_file(
        self,
        file_path: str,
        tags: Optional[list[str]] = None,
    ) -> dict:
        """导入本地文件"""
        tags = tags or []
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # 根据扩展名选择解析器
        suffix = path.suffix.lower()
        
        if suffix == ".pdf":
            result = await self.pdf_parser.parse_file(path)
            doc_type = DocumentType.PAPER
            raw_subdir = "papers"
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
        
        if not result.success:
            raise ValueError(f"Failed to parse file: {result.error}")
        
        # 保存文档
        doc_id = self._generate_id()
        doc_path = self.vault_path / "raw" / raw_subdir / f"{doc_id}.md"
        
        content = self._create_raw_markdown(
            id=doc_id,
            type=doc_type,
            title=result.title,
            content=result.content,
            source_url=str(path),
            tags=tags,
            metadata=result.metadata,
        )
        
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(content, encoding="utf-8")
        
        doc_create = DocumentCreate(
            type=doc_type,
            title=result.title,
            content=result.content,
            source_url=str(path),
            tags=tags,
            metadata=result.metadata,
            status="pending",
        )
        
        doc = await self.doc_repo.create(doc_create, str(doc_path.relative_to(self.vault_path)))
        
        return {
            "id": doc.id,
            "status": doc.status,
            "title": doc.title,
            "type": doc.type.value,
        }

    def _generate_id(self) -> str:
        return uuid4().hex[:12]

    def _create_raw_markdown(
        self,
        id: str,
        type: DocumentType,
        title: str,
        content: str,
        source_url: str,
        tags: list[str],
        metadata: dict,
    ) -> str:
        """创建原始 markdown 文件内容"""
        import yaml
        from datetime import datetime, timezone
        
        frontmatter = {
            "id": id,
            "type": type.value,
            "source": source_url,
            "title": title,
            "created": datetime.now(timezone.utc).isoformat(),
            "tags": tags,
            "status": "pending",
        }
        
        frontmatter.update(metadata)
        
        return f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---\n\n# {title}\n\n{content}"
```

- [ ] **Step 3: 创建导入路由**

```python
# backend/src/routers/ingest.py
"""导入路由"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.auth.dependencies import get_current_user, get_db
from src.models.user import User
from src.services.ingest import IngestService
from src.repositories.document_repo import DocumentRepository
from src.config import get_settings

router = APIRouter(prefix="/ingest", tags=["Ingest"])


class IngestUrlRequest(BaseModel):
    url: str
    tags: Optional[list[str]] = None


class IngestFileRequest(BaseModel):
    path: str
    tags: Optional[list[str]] = None


class ImportResult(BaseModel):
    id: str
    status: str
    title: str
    type: str


@router.post("/url", response_model=ImportResult)
async def ingest_url(
    request: IngestUrlRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    """导入 URL"""
    from pathlib import Path
    
    settings = get_settings()
    ingest_service = IngestService(
        vault_path=Path(settings.vault_path),
        doc_repo=DocumentRepository(db),
    )
    
    try:
        return await ingest_service.ingest_url(request.url, request.tags)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "IMPORT_FAILED", "message": str(e)}},
        )


@router.post("/file", response_model=ImportResult)
async def ingest_file(
    request: IngestFileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    """导入本地文件"""
    from pathlib import Path
    
    settings = get_settings()
    ingest_service = IngestService(
        vault_path=Path(settings.vault_path),
        doc_repo=DocumentRepository(db),
    )
    
    try:
        return await ingest_service.ingest_file(request.path, request.tags)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FILE_NOT_FOUND", "message": str(e)}},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "IMPORT_FAILED", "message": str(e)}},
        )
```

- [ ] **Step 4: 更新 conftest.py 添加 auth_headers fixture**

```python
# backend/tests/conftest.py 添加

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client(temp_vault, db):
    """创建测试客户端"""
    from src.database import Database
    
    app.state.db = db
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """获取认证 headers"""
    # 先设置账户
    client.post("/api/v1/auth/setup", json={"username": "admin", "password": "test-password-123"})
    
    # 登录获取 token
    login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "test-password-123"})
    token = login_resp.json()["token"]
    
    return {"Authorization": f"Bearer {token}"}
```

- [ ] **Step 5: 运行测试**

```bash
cd backend && python -m pytest tests/integration/test_ingest.py -v
```

- [ ] **Step 6: 提交**

```bash
git add backend/src/services/ingest.py backend/src/routers/ingest.py backend/tests/integration/test_ingest.py
git commit -m "feat: add ingest service and router"
```

---

## Phase 5: LLM 集成

### Task 5.1: LLM Client

**Files:**
- Create: `backend/src/llm/client.py`
- Create: `backend/src/utils/retry.py`
- Create: `backend/tests/unit/test_llm_client.py`
- Create: `backend/tests/vcr/` 目录

- [ ] **Step 1: 写 LLM Client 测试**

```python
# backend/tests/unit/test_llm_client.py
"""LLM Client 测试"""

import pytest

from src.llm.client import LLMClient


@pytest.fixture
def llm_client():
    return LLMClient()


def test_build_prompt(llm_client):
    """测试构建 prompt"""
    template = "Hello {name}, today is {day}."
    variables = {"name": "World", "day": "Monday"}
    
    result = llm_client._build_prompt(template, variables)
    
    assert result == "Hello World, today is Monday."
```

- [ ] **Step 2: 创建重试工具**

```python
# backend/src/utils/retry.py
"""重试工具"""

import asyncio
import functools
from typing import Callable, Type, Tuple

from loguru import logger


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """指数退避重试装饰器"""
    
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"All {max_retries} retries failed: {e}")
                        raise
                    
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay,
                    )
                    
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator
```

- [ ] **Step 3: 创建 LLM Client**

```python
# backend/src/llm/client.py
"""LLM Client"""

from typing import Any, AsyncGenerator, Optional

import litellm
from litellm import acompletion

from src.config import get_settings
from src.utils.retry import retry_with_backoff


class LLMClient:
    """LLM 客户端"""

    def __init__(self):
        self.settings = get_settings()
        self._setup_api_keys()

    def _setup_api_keys(self):
        """设置 API Keys"""
        if self.settings.gemini_api_key:
            litellm.api_key = self.settings.gemini_api_key
        # LiteLLM 会自动从环境变量读取其他 key

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """生成文本"""
        model = model or self.settings.llm_default_model
        
        response = await acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content

    async def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        model = model or self.settings.llm_default_model
        
        response = await acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _build_prompt(self, template: str, variables: dict[str, Any]) -> str:
        """构建 prompt"""
        return template.format(**variables)
```

- [ ] **Step 4: 运行测试**

```bash
cd backend && python -m pytest tests/unit/test_llm_client.py -v
```

- [ ] **Step 5: 提交**

```bash
git add backend/src/llm/client.py backend/src/utils/retry.py backend/tests/unit/test_llm_client.py
git commit -m "feat: add LLM client with retry support"
```

---

### Task 5.2: Prompt 模板

**Files:**
- Create: `backend/src/llm/prompts.py`
- Create: `backend/tests/unit/test_prompts.py`

- [ ] **Step 1: 创建 Prompt 模板**

```python
# backend/src/llm/prompts.py
"""Prompt 模板"""

from typing import Any


class PromptTemplates:
    """Prompt 模板集合"""
    
    COMPILE_DOCUMENT = """你是一个知识库编辑专家。请将以下原始文档编译成结构化的 Wiki 文章。

## 输出要求
- 输出语言: {output_language}
- 使用 Markdown 格式
- 生成摘要、关键概念、相关实体
- 使用 [[双向链接]] 标记重要概念

## 原始文档
标题: {document_title}
类型: {document_type}
来源: {document_source}
内容:
{document_content}

## 输出格式
请按以下格式输出:

# {{翻译后的标题}}

## 摘要
[2-3 句话总结文档核心内容]

## 核心内容
[结构化的主要内容，使用二级/三级标题组织]

## 关键概念
- [[概念1]]: 简要解释
- [[概念2]]: 简要解释
- [[概念3]]: 简要解释

## 相关来源
- [[{source_id}]] - {original_title}
"""

    EXTRACT_CONCEPTS = """你是一个知识图谱构建专家。请从以下文档中提取所有相关概念。

## 提取要求
- 输出语言: {output_language}
- 粒度: 细粒度（包含专有名词、专业术语、方法论、通用概念）
- 每个概念需给出: 名称、类型、置信度(0-1)、简要定义

## 文档内容
{document_content}

## 输出格式 (JSON)
{{
  "concepts": [
    {{
      "name": "概念名称",
      "type": "architecture|methodology|concept|entity|metric|dataset",
      "confidence": 0.95,
      "definition": "简要定义",
      "aliases": ["别名1", "别名2"]
    }}
  ]
}}
"""

    QA_ANSWER = """你是一个知识库助手。请基于以下检索到的文档回答用户问题。

## 用户问题
{question}

## 相关文档
{sources}

## 回答要求
1. 优先基于提供的文档内容回答
2. 如果文档信息不足以回答，明确说明
3. 在回答中使用 [[wiki-link]] 引用来源文档
4. 如果有相关概念，使用 [[概念名]] 标记
5. 回答末尾列出主要参考来源

## 输出格式

### 回答
[你的回答内容，使用 Markdown 格式]

### 参考来源
- [[{source_id_1}]] - {{title_1}}
- [[{source_id_2}]] - {{title_2}}

### 相关概念
[[概念1]] | [[概念2]] | [[概念3]]
"""

    @classmethod
    def compile_document(
        cls,
        document_title: str,
        document_type: str,
        document_source: str,
        document_content: str,
        source_id: str,
        original_title: str,
        output_language: str = "中文",
    ) -> str:
        """生成文档编译 prompt"""
        return cls.COMPILE_DOCUMENT.format(
            output_language=output_language,
            document_title=document_title,
            document_type=document_type,
            document_source=document_source,
            document_content=document_content,
            source_id=source_id,
            original_title=original_title,
        )

    @classmethod
    def extract_concepts(
        cls,
        document_content: str,
        output_language: str = "中文",
    ) -> str:
        """生成概念提取 prompt"""
        return cls.EXTRACT_CONCEPTS.format(
            output_language=output_language,
            document_content=document_content,
        )

    @classmethod
    def qa_answer(
        cls,
        question: str,
        sources: str,
        source_ids: list[str],
        titles: list[str],
    ) -> str:
        """生成问答 prompt"""
        return cls.QA_ANSWER.format(
            question=question,
            sources=sources,
            source_id_1=source_ids[0] if source_ids else "",
            source_id_2=source_ids[1] if len(source_ids) > 1 else "",
        )
```

- [ ] **Step 2: 写 Prompt 测试**

```python
# backend/tests/unit/test_prompts.py
"""Prompt 模板测试"""

from src.llm.prompts import PromptTemplates


def test_compile_document_prompt():
    """测试文档编译 prompt 生成"""
    prompt = PromptTemplates.compile_document(
        document_title="Test Title",
        document_type="web",
        document_source="https://example.com",
        document_content="Test content here.",
        source_id="abc123",
        original_title="Test Title",
        output_language="中文",
    )
    
    assert "Test Title" in prompt
    assert "Test content here." in prompt
    assert "中文" in prompt
    assert "[[abc123]]" in prompt


def test_extract_concepts_prompt():
    """测试概念提取 prompt 生成"""
    prompt = PromptTemplates.extract_concepts(
        document_content="This is about machine learning and AI.",
        output_language="中文",
    )
    
    assert "machine learning" in prompt
    assert "中文" in prompt
    assert '"concepts"' in prompt
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/unit/test_prompts.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/llm/prompts.py backend/tests/unit/test_prompts.py
git commit -m "feat: add prompt templates"
```

---

## Phase 8: 前端开发

### Task 8.1: 创建 React 项目

**Files:**
- Create: `frontend/` 目录结构

- [ ] **Step 1: 创建前端项目**

```bash
cd /path/to/your-project
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: 安装依赖**

```bash
cd frontend
npm install react-router-dom @tanstack/react-query lucide-react clsx
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 3: 配置 TailwindCSS**

```javascript
// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

```css
/* frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 4: 创建基础结构**

```tsx
// frontend/src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
```

- [ ] **Step 5: 提交**

```bash
git add frontend/
git commit -m "chore: init frontend project with Vite + React + TailwindCSS"
```

---

### Task 8.2: API 服务和认证

**Files:**
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/hooks/useAuth.ts`

- [ ] **Step 1: 创建 API 服务**

```typescript
// frontend/src/services/api.ts
const API_BASE = '/api/v1';

interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

class ApiService {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.error?.message || 'Request failed');
    }

    return response.json();
  }

  // Auth
  async setup(username: string, password: string) {
    return this.request<{ success: boolean }>('/auth/setup', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async login(username: string, password: string) {
    const data = await this.request<{ token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.token = data.token;
    return data;
  }

  // Documents
  async getDocuments(params?: { type?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.type) searchParams.set('type', params.type);
    if (params?.status) searchParams.set('status', params.status);
    
    const query = searchParams.toString();
    return this.request<{ total: number; items: any[] }>(`/documents${query ? '?' + query : ''}`);
  }

  // Ingest
  async ingestUrl(url: string, tags?: string[]) {
    return this.request<{ id: string; status: string }>('/ingest/url', {
      method: 'POST',
      body: JSON.stringify({ url, tags }),
    });
  }

  async ingestFile(path: string, tags?: string[]) {
    return this.request<{ id: string; status: string }>('/ingest/file', {
      method: 'POST',
      body: JSON.stringify({ path, tags }),
    });
  }

  // QA
  async askQuestion(question: string, stream: boolean = false) {
    if (stream) {
      const response = await fetch(`${API_BASE}/qa/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token}`,
        },
        body: JSON.stringify({ question, stream: true }),
      });
      return response.body;
    }
    
    return this.request<{ answer: string; sources: any[] }>('/qa/ask', {
      method: 'POST',
      body: JSON.stringify({ question, stream: false }),
    });
  }

  // System
  async getStatus() {
    return this.request<{ status: string; stats: any }>('/system/status');
  }
}

export const api = new ApiService();
```

- [ ] **Step 2: 创建 useAuth hook**

```typescript
// frontend/src/hooks/useAuth.ts
import { useState, useEffect } from 'react';
import { api } from '../services/api';

interface User {
  username: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSetupRequired, setIsSetupRequired] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.setToken(token);
      // Verify token
      api.getStatus().then(() => {
        setUser({ username: 'user' }); // TODO: get from token
        setLoading(false);
      }).catch(() => {
        localStorage.removeItem('token');
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    const { token } = await api.login(username, password);
    localStorage.setItem('token', token);
    api.setToken(token);
    setUser({ username });
  };

  const setup = async (username: string, password: string) => {
    await api.setup(username, password);
    await login(username, password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return { user, loading, login, logout, setup, isSetupRequired };
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/services/ frontend/src/hooks/
git commit -m "feat: add API service and auth hook"
```

---

## 执行计划总览

| Phase | 任务数 | 预计工时 |
|-------|--------|----------|
| Phase 1: 项目初始化 | 3 | 2h |
| Phase 2: 认证模块 | 3 | 3h |
| Phase 3: 数据层 | 2 | 2h |
| Phase 4: 导入模块 | 5 | 4h |
| Phase 5: LLM 集成 | 3 | 3h |
| Phase 6: 编译模块 | 4 | 4h |
| Phase 7: 问答模块 | 4 | 4h |
| Phase 8: 前端开发 | 6 | 8h |
| Phase 9: 集成测试 | 3 | 4h |
| **总计** | **33** | **34h** |

---

## 质量检查清单

实施完成后需要验证：

- [ ] 所有单元测试通过 (`pytest tests/unit -v`)
- [ ] 所有集成测试通过 (`pytest tests/integration -v`)
- [ ] 代码覆盖率 ≥ 80% (`pytest --cov --cov-fail-under=80`)
- [ ] 无硬编码配置（所有配置通过环境变量）
- [ ] 无非测试文件中的 Mock 数据
- [ ] LLM 测试使用 VCR 录制
- [ ] 前端构建成功 (`npm run build`)
- [ ] 前端测试通过 (`npm run test`)
- [ ] E2E 测试通过 (`npx playwright test`)
