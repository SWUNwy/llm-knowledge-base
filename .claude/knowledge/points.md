# 知识点库

> 细粒度知识单元，覆盖代码定位、业务术语、技术决策、常见陷阱、项目规范。

---

## 知识点列表

### KP-001: 后端入口与路由注册
| 字段 | 内容 |
|------|------|
| **触发关键词** | main.py, 应用入口, FastAPI 实例, 路由注册 |
| **知识点** | 后端入口在 `backend/src/main.py`，创建 FastAPI 实例后通过 `app.include_router(router, prefix="/api/v1")` 注册 9 个路由模块 |
| **相关文件** | `backend/src/main.py` |

### KP-002: 前端的 API 服务层
| 字段 | 内容 |
|------|------|
| **触发关键词** | api.ts, API 调用, fetch, axios |
| **知识点** | 前端通过 `frontend/src/services/api.ts` 中的 `api` 对象调用后端 API，统一管理 token 设置。基路径为 `/api/v1`。无额外 axios 依赖，使用原生 fetch |
| **相关文件** | `frontend/src/services/api.ts` |

### KP-003: 配置管理方式
| 字段 | 内容 |
|------|------|
| **触发关键词** | config.py, 环境变量, Settings, Pydantic |
| **知识点** | 后端使用 Pydantic Settings 管理配置，从 `.env` 文件加载。`lru_cache` 确保单例。所有 API Key 为 Optional，可配置多个 LLM 提供商 |
| **相关文件** | `backend/src/config.py` |

### KP-004: 统一错误处理机制
| 字段 | 内容 |
|------|------|
| **触发关键词** | AppError, ErrorCode, 错误处理, 异常 |
| **知识点** | 自定义 `AppError` 接收 `ErrorCode` 枚举 + detail 字符串。FastAPI 异常处理器转换为统一 JSON 格式 `{"error": {"code": "...", "message": "..."}}`。前端有对应的 `ApiError` 类 |
| **相关文件** | `backend/src/errors.py`, `backend/src/middleware/error_handler.py`, `frontend/src/services/api.ts` |

### KP-005: 双模式认证架构
| 字段 | 内容 |
|------|------|
| **触发关键词** | 认证, 登录, auth, JWT, cloud |
| **知识点** | 项目支持两种认证模式：local（本地 SQLite 用户 + JWT）和 cloud（通过 Cloud API 登录 + License 令牌）。前端 `useAuth` hook 管理两种模式，localStorage 持久化 token |
| **相关文件** | `backend/src/auth/`, `frontend/src/hooks/useAuth.ts` |

### KP-006: 统一解析层 MarkItDown
| 字段 | 内容 |
|------|------|
| **触发关键词** | MarkItDown, 解析, parser, 文件转换 |
| **知识点** | 所有文档解析统一走 Microsoft MarkItDown 引擎，支持 PDF/DOCX/PPTX/XLSX/CSV/EPUB/HTML/图片等 15+ 格式，输出均为 Markdown。代码中对应的 Parser 类在 `backend/src/parsers/markitdown.py` |
| **相关文件** | `backend/src/parsers/markitdown.py`, `backend/src/services/processor.py` |

### KP-007: LiteLLM 统一 LLM 接口
| 字段 | 内容 |
|------|------|
| **触发关键词** | LLM, 模型调用, LiteLLM, Gemini, OpenAI |
| **知识点** | 后端使用 LiteLLM 库统一调用不同 LLM 提供商（OpenAI/Gemini/Anthropic/Ollama）。`llm_default_model` 配置格式为 `provider/model`（如 `gemini/gemini-pro`） |
| **相关文件** | `backend/src/llm/client.py` |

### KP-008: Format-Aware Prompt 模板
| 字段 | 内容 |
|------|------|
| **触发关键词** | Prompt, 编译模板, COMPILE_DOCUMENT, 提示词 |
| **知识点** | 不同文档类型走不同 Prompt 模板：PDF 论文 → COMPILE_PAPER（学术结构），PPTX → COMPILE_PRESENTATION（叙事流），表格 → COMPILE_TABLE_DATA（数据精度）。模板集中在 `PromptTemplates` 类 |
| **相关文件** | `backend/src/llm/prompts.py` |

### KP-009: SQLite + FTS5 全文搜索
| 字段 | 内容 |
|------|------|
| **触发关键词** | 全文搜索, FTS5, SQLite, 检索 |
| **知识点** | 后端使用 SQLite FTS5 虚拟表实现全文搜索，分词器为 `porter unicode61`。文档的 FTS 内容在 `documents_fts` 表中，搜索通过 `documents_fts MATCH ?` 实现 |
| **相关文件** | `backend/src/database.py`（_create_tables 方法） |

### KP-010: Obsidian 原生输出
| 字段 | 内容 |
|------|------|
| **触发关键词** | Obsidian, wiki, vault, Markdown, 双向链接 |
| **知识点** | 编译结果输出为带 `[[wiki-links]]` 的 Obsidian 兼容 Markdown 文件。用户数据就是文件夹里的 Markdown，兼容 Obsidian 生态。`VAULT_PATH` 指向本地 Obsidian 文件夹 |
| **相关文件** | `backend/src/config.py`, `backend/src/services/compile.py` |

### KP-011: 沙漏型数据流（Flywheel 闭环）
| 字段 | 内容 |
|------|------|
| **触发关键词** | 数据流, 飞轮, pipeline, 导入编译问答 |
| **知识点** | 核心数据流为 Collect → Parse (MarkItDown) → Compile (LLM) → Wiki (Obsidian) → Ask & Save Back 的闭环。导入、编译、问答三条 Pipeline 在代码中对应三个 Service 类 |
| **相关文件** | `backend/src/services/ingest.py`, `backend/src/services/compile.py`, `backend/src/services/qa.py` |

### KP-012: 前端路由与页面组织
| 字段 | 内容 |
|------|------|
| **触发关键词** | 前端路由, 页面, react-router, Import/Library/Chat |
| **知识点** | 前端使用 React Router v7 的 BrowserRouter，6 个页面（Login/Setup/Import/Library/Chat/Settings/Concepts），受保护路由通过 ProtectedRoute 组件包裹 Layout |
| **相关文件** | `frontend/src/App.tsx` |

### KP-013: 官网 Next.js App Router 结构
| 字段 | 内容 |
|------|------|
| **触发关键词** | 官网, website, landing page, Next.js |
| **知识点** | 官网是独立的 Next.js 16 项目，使用 App Router。首页由 Navbar / Hero / PainPoints / Features / Flow / Pricing / CTA / Footer 组件构成。另有 auth（register/login）、stripe checkout/webhook、license verify 等 API 路由 |
| **相关文件** | `website/app/` |

### KP-014: License 管理与计费体系
| 字段 | 内容 |
|------|------|
| **触发关键词** | License, Stripe, 计费, 订阅, usage |
| **知识点** | 本地 App 启动时验证 License（`LicenseManager`），缓存到 `.license_token` 文件。官网使用 Stripe Checkout 处理支付，webhook 同步订阅状态到 PostgreSQL。三层定价：trial / personal（49/月） / professional（99/月） / team（299/月） |
| **相关文件** | `backend/src/license/manager.py`, `website/app/api/stripe/`, `website/lib/stripe.ts` |

### KP-015: Docker 部署配置
| 字段 | 内容 |
|------|------|
| **触发关键词** | Docker, docker-compose, 部署, 容器 |
| **知识点** | 项目根目录有 Dockerfile（多阶段构建 backend + frontend）和 docker-compose.yml（backend + frontend 两个服务）。backend 使用 SQLite 卷持久化，frontend 通过 Nginx 代理后端 API |
| **相关文件** | `Dockerfile`, `docker-compose.yml`, `docker/nginx.conf` |

### KP-016: 代码规范与工具链
| 字段 | 内容 |
|------|------|
| **触发关键词** | ruff, mypy, eslint, pytest, 代码规范 |
| **知识点** | Python 使用 ruff（行长度 100, 启用 isort/bugbear/comprehensions/simplify）+ mypy strict mode。TypeScript 使用 eslint + typescript-eslint。测试使用 pytest（覆盖率 ≥80%）+ VCR 录制回放 LLM 调用 |
| **相关文件** | `backend/pyproject.toml`, `frontend/eslint.config.js` |

### KP-017: Vite 代理配置
| 字段 | 内容 |
|------|------|
| **触发关键词** | Vite proxy, 开发代理, 跨域 |
| **知识点** | 开发模式下，Vite 将 `/api` 请求代理到 `http://127.0.0.1:8000`，前后端无跨域问题。配置在 `frontend/vite.config.ts` 的 `server.proxy` |
| **相关文件** | `frontend/vite.config.ts` |

---

## 知识点索引

| 编号 | 类型 | 关键词 |
|------|------|--------|
| KP-001 | 代码定位 | main.py, 路由注册, FastAPI 入口 |
| KP-002 | 代码定位 | api.ts, API 调用, 前端服务层 |
| KP-003 | 代码定位 | config.py, 环境变量, Pydantic Settings |
| KP-004 | 代码定位 | AppError, ErrorCode, 错误处理链 |
| KP-005 | 技术决策 | 双模式认证, JWT, Cloud Auth |
| KP-006 | 技术决策 | MarkItDown, 统一解析, 15+ 格式 |
| KP-007 | 技术决策 | LiteLLM, 多模型支持 |
| KP-008 | 技术决策 | Format-Aware Prompt, 文档类型模板 |
| KP-009 | 技术决策 | SQLite FTS5, 全文搜索 |
| KP-010 | 技术决策 | Obsidian 兼容, wiki-links |
| KP-011 | 业务术语 | 数据飞轮, 三 Pipeline |
| KP-012 | 代码定位 | 前端路由, 6 个页面 |
| KP-013 | 代码定位 | Next.js App Router, 官网结构 |
| KP-014 | 业务术语 | License, Stripe, 定价 |
| KP-015 | 项目规范 | Docker, docker-compose 部署 |
| KP-016 | 项目规范 | ruff, mypy, pytest 规范 |
| KP-017 | 项目规范 | Vite 代理, 跨域开发配置 |

---

*由 Project Knowledge 于 2026-05-26 自动生成*
