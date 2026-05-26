# 数据库知识

> 本文档沉淀 LLM Knowledge Base 项目的数据库相关知识。

---

## 一、数据库配置

| 配置项 | 后端（主应用） | 官网（SaaS） |
|--------|--------------|-------------|
| 数据库 | SQLite + FTS5 | PostgreSQL |
| 连接方式 | `aiosqlite` async driver | `pg` (node-postgres) Pool |
| 连接池 | SQLite 单连接 | Pool（默认配置） |
| 文件路径 | `{VAULT_PATH}/.wiki/metadata.db` | `DATABASE_URL` 环境变量 |
| SSL | — | 生产环境 `rejectUnauthorized: false` |

## 二、表结构规范

### 命名规范
| 规则 | 示例 |
|------|------|
| 表名 | snake_case 复数 | `documents`, `compile_tasks` |
| 字段 | snake_case | `created_at`, `password_hash` |
| 主键 | `id TEXT PRIMARY KEY` | `doc-abc123` 格式 |
| 外键 | snake_case + `_id` 后缀 | `doc_id`, `concept_id` |
| 时间戳 | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | `created_at`, `updated_at` |

### SQLite 特殊配置
- **外键**: `PRAGMA foreign_keys = ON`（需手动启用）
- **行工厂**: `sqlite3.Row`（支持 dict-like 访问）
- **全文搜索**: FTS5 虚拟表，分词器 `porter unicode61`
- **数据类型**: 使用 TEXT 存储 JSON（如 `metadata`, `sources` 字段）

## 三、主要表结构

### 后端（SQLite）

#### 1. users
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
说明：存储本地认证用户。password_hash 使用 bcrypt 算法。

#### 2. documents
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    path TEXT NOT NULL,
    title TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}'
);
```
说明：存储文档元信息。type 值为 web/paper/video/code。metadata 为 JSON 字符串。

#### 3. documents_fts（FTS5 虚拟表）
```sql
CREATE VIRTUAL TABLE documents_fts USING fts5(
    id, title, content,
    tokenize='porter unicode61'
);
```
说明：文档内容的全文搜索索引。不存储原始文档内容，只存 FTS 索引。

#### 4. concepts
```sql
CREATE TABLE concepts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    wiki_path TEXT,
    mention_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
说明：从文档中提取的知识概念。wiki_path 指向 Obsidian vault 中的对应页面。

#### 5. doc_concepts
```sql
CREATE TABLE doc_concepts (
    doc_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    relevance_score REAL DEFAULT 0.0,
    PRIMARY KEY (doc_id, concept_id),
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE
);
```
说明：文档和概念的多对多关联，带相关性分数。

#### 6. links
```sql
CREATE TABLE links (
    from_path TEXT NOT NULL,
    to_path TEXT NOT NULL,
    link_type TEXT NOT NULL DEFAULT 'explicit',
    confidence REAL DEFAULT 1.0,
    PRIMARY KEY (from_path, to_path, link_type)
);
```
说明：文档间的双向链接，支持显式（用户创建）和隐式（系统推断）链接。

#### 7. compile_tasks
```sql
CREATE TABLE compile_tasks (
    id TEXT PRIMARY KEY,
    status TEXT DEFAULT 'pending',
    total_docs INTEGER DEFAULT 0,
    completed_docs INTEGER DEFAULT 0,
    failed_docs INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result TEXT
);
```
说明：跟踪异步编译任务进度。result 为 JSON 字符串存储编译结果摘要。

#### 8. qa_history
```sql
CREATE TABLE qa_history (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
说明：QA 问答历史记录。sources 为 JSON 数组字符串，存储引用文档列表。

### 官网（PostgreSQL）

官网使用 PostgreSQL，通过 `website/db/schema.sql` 创建 6 张表：
- `users` — 邮箱认证用户
- `subscriptions` — Stripe 订阅管理
- `license_tokens` — 设备 License 令牌
- `usage_logs` — API 使用记录
- `tier_limits` — 定价层级限制配置
- `releases` — 桌面应用发布版本

## 四、迁移规范

### 后端（SQLite）
- **迁移文件位置**：无迁移框架，表结构在 `backend/src/database.py` 的 `_create_tables()` 方法中定义
- **建表方式**：使用 `CREATE TABLE IF NOT EXISTS`，代码即 schema
- **初始化时机**：应用启动时 `startup` 事件中自动创建

### 官网（PostgreSQL）
- **迁移文件位置**：`website/db/schema.sql`（完整 schema）
- **迁移方式**：手动执行 `psql $DATABASE_URL -f website/db/schema.sql`
- **迁移记录**：`website/db/migrations/001_initial.sql`（指向 schema.sql）

## 五、索引策略

### 后端索引
| 表 | 索引类型 | 说明 |
|-----|---------|------|
| documents_fts | FTS5 全文索引 | porter unicode61 分词器 |
| 外键约束 | 自动索引 | doc_concepts.doc_id, doc_concepts.concept_id |

### 官网索引
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_license_tokens_user_id ON license_tokens(user_id);
CREATE INDEX idx_license_tokens_token_hash ON license_tokens(token_hash);
CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_timestamp ON usage_logs(timestamp);
```

## 六、常用查询模式

```python
# 全文搜索
cursor = await self._conn.execute(
    "SELECT * FROM documents_fts WHERE documents_fts MATCH ?",
    (query,)
)

# 文档列表 + 分页
cursor = await self._conn.execute(
    "SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?",
    (limit, offset)
)

# 文档-概念关联查询
cursor = await self._conn.execute(
    """SELECT c.* FROM concepts c
       JOIN doc_concepts dc ON c.id = dc.concept_id
       WHERE dc.doc_id = ?""",
    (doc_id,)
)
```

---

*由 Project Knowledge 于 2026-05-26 自动生成*
