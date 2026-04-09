# R001 - 技术设计

## 概述

本地优先的 LLM 知识库应用，采用 FastAPI 后端 + React 前端，数据存储在 Obsidian 兼容的本地文件系统 + SQLite 索引。

## 架构图

```
┌────────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │  导入    │ │  文库    │ │  问答    │ │  设置    │              │
│  │  Center  │ │  View    │ │  Chat    │ │  Panel   │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
└────────────────────────────────────────────────────────────────────┘
                              │ REST API / SSE
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Backend (Python FastAPI)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                  │
│  │ Ingestion   │ │ Compilation │ │ Q&A Engine  │                  │
│  │ Service     │ │ Service     │ │             │                  │
│  └─────────────┘ └─────────────┘ └─────────────┘                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                  │
│  │ Parser      │ │ LLM Client  │ │ Indexer     │                  │
│  │ (多格式)    │ │ (LiteLLM)   │ │ (SQLite)    │                  │
│  └─────────────┘ └─────────────┘ └─────────────┘                  │
└────────────────────────────────────────────────────────────────────┘
                              │ File System I/O
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Obsidian Vault (本地文件夹)                    │
│  ├── .wiki/              # 产品元数据 (SQLite + config)             │
│  ├── raw/                # 原始资料 (web/papers/videos/code)        │
│  ├── wiki/               # LLM 编译的知识库                         │
│  └── outputs/            # 生成的输出 (answers/slides)              │
└────────────────────────────────────────────────────────────────────┘
```

## 组件设计

### 1. Ingestion Service（导入服务）

- **职责**：接收导入请求，识别来源类型，调用对应解析器，存储结果
- **接口**：
  ```python
  async def import_url(url: str, tags: List[str]) -> ImportResult
  async def import_file(path: str, tags: List[str]) -> ImportResult
  async def import_video(url: str, tags: List[str]) -> ImportResult
  async def import_github(repo_url: str, branch: str, tags: List[str]) -> ImportResult
  ```
- **依赖**：Parser 模块、Document Repository、Indexer

### 2. Compilation Service（编译服务）

- **职责**：读取原始文档，调用 LLM 编译成 Wiki，提取概念，生成链接
- **接口**：
  ```python
  async def compile_documents(doc_ids: List[str], options: CompileOptions) -> CompileResult
  async def get_task_status(task_id: str) -> TaskStatus
  ```
- **依赖**：LLM Client、Document Repository、Concept Repository

### 3. Q&A Engine（问答引擎）

- **职责**：接收问题，检索相关文档，调用 LLM 生成回答
- **接口**：
  ```python
  async def ask(question: str, options: QAOptions) -> AsyncGenerator[QAChunk, None]
  async def save_answer(question: str, answer: str, sources: List[str]) -> SaveResult
  ```
- **依赖**：Indexer（检索）、LLM Client

### 4. LLM Client（LLM 客户端）

- **职责**：统一 LLM 调用接口，处理重试、限流、错误
- **接口**：
  ```python
  async def generate(prompt: str, config: LLMConfig) -> LLMResponse
  async def stream(prompt: str, config: LLMConfig) -> AsyncGenerator[str, None]
  async def embed(text: str) -> List[float]
  ```
- **依赖**：LiteLLM 库

### 5. Indexer（索引服务）

- **职责**：维护全文索引、向量索引，提供检索能力
- **接口**：
  ```python
  async def index_document(doc: Document) -> None
  async def search(query: str, limit: int) -> List[SearchResult]
  async def vector_search(embedding: List[float], limit: int) -> List[SearchResult]
  ```
- **依赖**：SQLite FTS5、SQLite-vec

## 数据模型

### SQLite 表结构

```sql
-- 文档表
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    type TEXT,           -- web/paper/video/code
    path TEXT,
    title TEXT,
    status TEXT,         -- pending/processed
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    metadata JSON
);

-- 全文搜索
CREATE VIRTUAL TABLE documents_fts USING fts5(
    id, title, content,
    content='documents'
);

-- 向量索引 (Phase 2)
CREATE VIRTUAL TABLE vec_documents USING vec0(
    doc_id TEXT PRIMARY KEY,
    embedding FLOAT[1536],
    chunk_index INTEGER
);

-- 概念表
CREATE TABLE concepts (
    id TEXT PRIMARY KEY,
    name TEXT,
    wiki_path TEXT,
    mention_count INTEGER,
    created_at TIMESTAMP
);

-- 文档-概念关联
CREATE TABLE doc_concepts (
    doc_id TEXT,
    concept_id TEXT,
    relevance_score REAL,
    PRIMARY KEY (doc_id, concept_id)
);

-- 链接关系
CREATE TABLE links (
    from_path TEXT,
    to_path TEXT,
    link_type TEXT,      -- explicit/inferred
    confidence REAL,
    PRIMARY KEY (from_path, to_path)
);
```

### Markdown 文件格式

**Raw 文档**（`raw/{type}/{id}.md`）：
```markdown
---
id: abc123
type: web
source: https://example.com/article
title: Article Title
created: 2024-01-15
tags: [tag1, tag2]
status: pending
---

# Article Title

[原始正文内容...]
```

**Wiki 文档**（`wiki/{category}/{id}.md`）：
```markdown
---
id: wiki-001
source_ids: [abc123]
created: 2024-01-16
tags: [auto-generated]
---

# Concept Name

## 摘要
[2-3 句话总结]

## 核心内容
[结构化内容]

## 关键概念
- [[概念1]]: 简要解释
- [[概念2]]: 简要解释

## 相关来源
- [[abc123]] - 原文档标题
```

## API 设计

详见 `docs/design.md` 中的 API 接口设计章节。

核心端点：
- `POST /api/v1/auth/login` - 登录
- `POST /api/v1/ingest/url` - 导入 URL
- `POST /api/v1/ingest/file` - 导入文件
- `POST /api/v1/compile` - 触发编译
- `POST /api/v1/qa/ask` - 提问
- `GET /api/v1/documents` - 文档列表
- `GET /api/v1/documents/search` - 搜索文档

## 错误处理

### 重试策略

| 场景 | 策略 |
|------|------|
| LLM 网络超时 | 指数退避重试，最多 3 次 |
| LLM 限流 (429) | 等待 retry-after 后重试 |
| 导入网络错误 | 重试 3 次 |
| 编译部分失败 | 保留成功，记录失败，支持重试 |

### 错误码

| 错误码 | HTTP | 说明 |
|--------|------|------|
| UNAUTHORIZED | 401 | 未登录 |
| VALIDATION_ERROR | 400 | 参数错误 |
| IMPORT_FAILED | 400 | 导入失败 |
| COMPILE_FAILED | 500 | 编译失败 |
| LLM_ERROR | 502 | LLM 调用失败 |
| FILE_NOT_FOUND | 404 | 文件不存在 |
| UNSUPPORTED_FORMAT | 400 | 格式不支持 |

## 性能优化

### 目标

| 操作 | 目标时间 |
|------|----------|
| 单文档导入 | < 5s |
| 单文档编译 | < 30s |
| 全文检索 | < 500ms |
| 问答响应 | < 2s |
| 系统启动 | < 3s |

### 策略

1. **检索优化**
   - FTS + 向量混合检索
   - 热门查询缓存
   - Embedding 缓存

2. **并发控制**
   - 最大 3 个并发任务
   - 任务优先级队列

3. **大文件处理**
   - PDF > 50MB：流式读取
   - 内容分块处理

4. **LLM 优化**
   - 并行处理多文档
   - Prompt 长度智能裁剪

## 安全考虑

1. **认证**：用户名密码 + JWT Token
2. **本地访问**：仅监听 localhost
3. **API Key**：存储在环境变量，不落盘
4. **文件访问**：限制在 vault 目录内

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LLM API 不稳定 | 编译/问答失败 | 自动重试 + 多模型备用 |
| 大文件内存溢出 | 导入失败 | 流式处理 + 分块 |
| 并发过高资源耗尽 | 系统崩溃 | 有限并发 + 任务队列 |
| 向量索引膨胀 | 检索变慢 | Phase 2 分区策略 |
