# 架构知识

> 本文档沉淀 LLM Knowledge Base 项目的架构相关知识。

---

## 一、项目结构

```
llm-knowledge-base/
├── backend/                  # Python FastAPI 后端
│   ├── src/
│   │   ├── main.py           # FastAPI 应用入口，注册 9 个路由
│   │   ├── config.py         # Pydantic Settings 配置管理
│   │   ├── database.py       # SQLite + FTS5 数据库管理
│   │   ├── errors.py         # 统一错误码和异常类
│   │   ├── auth/             # 认证模块（local JWT + cloud）
│   │   ├── license/          # License 管理与本地计数
│   │   ├── llm/              # LLM 客户端（LiteLLM + Cloud Proxy）
│   │   ├── models/           # Pydantic 数据模型
│   │   ├── parsers/          # 文档解析器（MarkItDown 统一入口）
│   │   ├── repositories/     # 数据访问层
│   │   ├── routers/          # 9 个 API 路由模块
│   │   ├── services/         # 业务逻辑层（ingest/compile/qa）
│   │   ├── middleware/       # FastAPI 中间件
│   │   └── utils/            # 工具函数
│   ├── tests/
│   │   ├── unit/             # 单元测试（16 个文件）
│   │   └── integration/      # 集成测试（5 个文件）
│   └── pyproject.toml        # Python 项目配置
├── frontend/                 # React + Vite 前端
│   ├── src/
│   │   ├── App.tsx           # 路由配置，6 个页面
│   │   ├── components/       # Layout, ProtectedRoute, ErrorAlert
│   │   ├── hooks/            # useAuth (认证状态管理)
│   │   ├── pages/            # 6 个页面组件
│   │   ├── services/         # api.ts, cloudApi.ts
│   │   └── lib/              # errorMessages.ts
│   └── e2e/                  # Playwright E2E 测试
├── website/                  # Next.js 官网（独立项目）
│   ├── app/
│   │   ├── page.tsx          # 首页（Hero/Features/Pricing/CTA）
│   │   ├── dashboard/        # 用户仪表盘
│   │   ├── login/            # 登录页
│   │   ├── register/         # 注册页
│   │   └── api/              # API 路由（auth/stripe/license/llm/usage）
│   ├── components/           # UI 组件（hero/features/pricing/footer...）
│   └── lib/                  # 工具库（db/auth/stripe/llm）
├── docker/
│   └── nginx.conf            # Nginx 反代配置
├── docker-compose.yml        # 本地开发编排
├── Dockerfile                # 多阶段构建
└── scripts/                  # dev/setup/test/export-api 脚本
```

## 二、技术栈

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.9 | 运行时 |
| FastAPI | — | Web 框架 |
| SQLite + aiosqlite | — | 数据库 |
| FTS5 | — | 全文搜索 |
| LiteLLM | — | 统一 LLM 调用接口 |
| Pydantic | v2 | 数据验证 + 配置管理 |
| python-jose | — | JWT 令牌 |
| bcrypt | — | 密码哈希 |
| MarkItDown | — | 15+ 格式统一解析 |
| httpx | — | HTTP 客户端（Cloud API） |
| ruff | — | Python linter |
| mypy | strict | 类型检查 |
| pytest | — | 测试框架 |
| VCR.py | — | LLM 调用录制回放 |

### 前端（SPA）
| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19 | UI 框架 |
| TypeScript | ~6.0 | 类型系统 |
| Vite | 6 | 构建工具 |
| TailwindCSS | 4 | 样式 |
| React Router | v7 | 路由 |
| TanStack React Query | v5 | 服务端状态管理 |
| lucide-react | — | 图标库 |
| Playwright | — | E2E 测试 |

### 官网（SaaS）
| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16 | React 元框架 |
| TypeScript | ^5 | 类型系统 |
| TailwindCSS | 3 | 样式 |
| PostgreSQL | — | 数据库 |
| Stripe | — | 支付处理 |
| Framer Motion | — | 动画 |
| jsonwebtoken | — | JWT |
| bcryptjs | — | 密码哈希 |
| openai | SDK | LLM 代理 |

### 工具链
| 工具 | 用途 |
|------|------|
| Docker | 容器化部署 |
| docker-compose | 本地开发编排 |
| ESLint | JS/TS 代码检查 |
| pre-commit | Git 钩子 |

## 三、认证方案

### 本地模式（Local）
1. 用户在 Setup 页面创建首个本地用户
2. 密码 bcrypt 哈希，存入 SQLite `users` 表
3. 登录返回 JWT token（HS256, 24h 过期），存入 localStorage
4. 后续请求在 Authorization header 携带 token

### Cloud 模式（SaaS）
1. 用户在官网注册 → 跳转 Stripe 付费 → 获取 License Token
2. 本地 App 通过 Cloud API 登录，获取 access_token + license_token
3. 每次请求验证 license_token + JWT
4. License 缓存到 `.license_token` 文件，离线时有 24h 宽限期

#### 相关文件
- 后端认证: `backend/src/auth/`（router, service, jwt, password, cloud_auth, dependencies）
- 前端认证: `frontend/src/hooks/useAuth.ts`, `frontend/src/services/cloudApi.ts`
- 官网认证: `website/lib/auth.ts`, `website/app/api/auth/`

## 四、实体关系

| 实体 | 说明 | 关键字段 |
|------|------|---------|
| Document | 导入的文档，可被编译和搜索 | id, type, path, title, status |
| Concept | 从文档中提取的概念/词条 | id, name, wiki_path, mention_count |
| User | 本地用户 | id, username, password_hash |
| Link | 文档间双向链接 | from_path, to_path, link_type |
| CompileTask | 异步编译任务跟踪 | id, status, total_docs, completed_docs |
| QAHistory | 问答历史记录 | id, question, answer, sources |
| Subscription | Stripe 订阅（官网 PostgreSQL） | id, user_id, tier, status, stripe_subscription_id |
| LicenseToken | 设备许可证令牌（官网 PostgreSQL） | id, user_id, token_hash, device_name |
| UsageLog | API 使用记录（官网 PostgreSQL） | id, user_id, action, tokens_used |
| Release | 发布版本下载（官网 PostgreSQL） | version, download_url_mac, download_url_win |

## 五、核心数据流

```
导入 Pipeline:
  [URL/文件/视频/GitHub] → MarkItDown 解析 → Markdown → DocumentProcessor
  → 存储文档 → FTS5 索引 → 概念提取 → 保存到 SQLite

编译 Pipeline:
  [文档列表] → PromptTemplates 按类型选模板 → LiteLLM 调用 LLM
  → Markdown 输出 → [[wiki-links]] 处理 → 写入 Obsidian vault

问答 Pipeline:
  [问题] → FTS5 全文检索 → 上下文构建 → PromptTemplates.qa_answer
  → LiteLLM 调用 LLM → SSE 流式响应 → [可选] 答案保存回库
```

---

*由 Project Knowledge 于 2026-05-26 自动生成*
