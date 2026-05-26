# LLM Knowledge Base 知识库索引

> 知识库是组织化的知识存储体系，用于解决通用大模型无法覆盖的专有知识召回问题。

---

## 知识库结构

```
knowledge/
├── INDEX.md           # 本文件 — 知识库索引
├── points.md          # 知识点库（细粒度知识单元）
├── term-mapping.md    # 术语映射表
└── kbase/             # 知识库文档
    ├── architecture.md    # 架构知识
    ├── api-design.md      # API 设计知识
    ├── database.md        # 数据库知识
    └── frontend.md        # 前端知识
```

## 双路召回机制

### 1. KBase 语义召回
- **方式**：向量检索找「语义相关」的内容
- **适用**：模糊需求场景（如"怎么导入文档"、"编译流程是什么"）
- **特点**：覆盖面广，可能包含噪音

### 2. 索引导航式召回
- **方式**：先筛选文档 → 再精确搜索
- **适用**：精确定位场景（如"Database 类在哪"、"API 路由前缀是什么"）
- **特点**：可追溯、可解释

## 知识库目录

### 架构知识 (architecture.md)
| 主题 | 描述 |
|------|------|
| 项目结构 | 三项目架构：backend/ + frontend/ + website/ |
| 技术栈 | Python FastAPI + React Vite + Next.js |
| 认证方案 | 双模式：本地 JWT + Cloud SaaS |
| 实体关系 | Document / Concept / User / Link / Subscription |

### API 设计知识 (api-design.md)
| 主题 | 描述 |
|------|------|
| RESTful 规范 | `/api/v1/{resource}` 前缀，snake_case 字段 |
| 字段转换 | 数据库 snake_case → API snake_case（不转换） |
| 错误处理 | `{"error": {"code": "...", "message": "..."}}` 统一格式 |
| 认证中间件 | JWT 令牌 + License 令牌双认证 |

### 数据库知识 (database.md)
| 主题 | 描述 |
|------|------|
| 表结构设计 | SQLite + FTS5（后端）、PostgreSQL（官网） |
| 迁移流程 | 手动 DDL 创建，无迁移框架 |
| 索引策略 | FTS5 全文索引 + 外键索引 |
| 查询优化 | FTS5 porter unicode61 分词器 |

### 前端知识 (frontend.md)
| 主题 | 描述 |
|------|------|
| 组件规范 | 函数组件 + Hooks，无 class 组件 |
| 样式规范 | TailwindCSS 4（前端）、TailwindCSS 3（官网） |
| 状态管理 | TanStack React Query 服务端状态 + localStorage 持久化 |
| 认证模式 | 自定义 useAuth hook，localStorage token 存储 |

## 知识召回触发

| 关键词 | 召回知识库 |
|--------|-----------|
| API、接口、路由、端点 | api-design.md |
| 数据库、表、SQL、Query | database.md |
| 组件、页面、样式、Hook | frontend.md |
| 架构、目录、结构、分层 | architecture.md |
| 认证、登录、JWT、Token | architecture.md, api-design.md |
| 编译、Compile、Prompt | architecture.md |
| 导入、Ingest、Parser | architecture.md |
| 文档、Document、概念、Concept | term-mapping.md |
| 错误处理、Error、异常 | api-design.md |
| 部署、Docker、容器 | architecture.md |

---

*由 Project Knowledge 于 2026-05-26 自动生成*
