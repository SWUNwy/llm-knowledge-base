# LLM Knowledge Base - 项目全景复盘

> 更新日期：2026-04-09
> 状态：Phase 3 实施开发待完成

---

## 一、项目定位

**一句话**：将零散资料（网页/PDF/视频/代码）自动编译成 Obsidian 知识库，并用 LLM 驱动问答。

**目标用户**：研究者、终身学习者、知识工作者。

**产品愿景**：先打造一套可用的个人工具，后续根据发展决定开源或商业化路径。

---

## 二、当前开发状态

### 2.1 各模块进度

| 模块 | 技术栈 | 代码量 | 状态 |
|------|--------|--------|------|
| 后端 | Python FastAPI + SQLite/FTS5 + LiteLLM | ~17K 行 | 骨架已搭建，核心业务逻辑未完成 |
| 前端 | React 18 + Vite + TailwindCSS + React Query | ~5.6K 行 | 6 个页面骨架已有，功能未接通 |
| 官网 | Next.js + TypeScript + TailwindCSS + Framer Motion | - | Phase 1 MVP 已完成 |
| 测试 | Pytest + 计划 Playwright E2E | 17 个文件 | 单元/集成测试框架已建，覆盖率待提升 |
| 文档/规范 | proposal + design + tasks + API spec | - | 完整 |

### 2.2 后端模块明细

已搭建的 Router（9 个）：
- `auth` — 用户注册/登录，JWT
- `ingest` — URL/PDF/视频/GitHub 导入
- `compile` — 文档编译触发与状态查询
- `qa` — 知识库问答
- `documents` — 文档 CRUD 与搜索
- `concepts` — 概念词条管理
- `settings` — LLM 提供商配置、API Key 管理
- `prompts` — Prompt 模板管理
- `system` — 系统状态

Parser（4 种）：web、pdf、video、github

### 2.3 前端页面明细

6 个页面：Login、Setup、Import、Library、Chat、Settings、Concepts

### 2.4 官网（Website）

已完成：Hero、Features、Pricing（3 档）、CTA、Footer + SEO 优化 + 滚动动画
独立 Next.js 项目，尚未与主应用串联。

---

## 三、核心价值链

### 3.1 三步飞轮

```
收集（导入） → 编译（LLM 重写） → 问答（检索+生成）
  ↑                                  │
  └──── 答案沉淀回库（自增强）──────────┘
```

### 3.2 价值拆解

| 层级 | 价值 | 差异化 |
|------|------|--------|
| 多源统一导入 | URL/PDF/视频/GitHub 一键入库，统一存为 Markdown | 不只是导入，是提取+结构化 |
| LLM 自动编译 | 原始文档 → 带 `[[双向链接]]` 的 Wiki 文章 + 概念提取 | **核心壁垒**：不是存下来，而是用 LLM 重写成知识网络 |
| 基于知识库问答 | 对已有知识提问，答案可沉淀回库 | 答案有来源引用，沉淀后知识库越来越强 |
| 本地优先 + Obsidian | 数据就是文件夹里的 Markdown，兼容 Obsidian 生态 | 用户不被锁定，Graph View/Dataview 等插件可用 |

### 3.3 竞争力判断

核心竞争力不在单一功能，在于闭环组合：

1. **"编译"而非"索引"** — Readwise/Notion AI 做检索增强，本项目做知识重写
2. **Obsidian 原生** — 输出标准 Markdown + `[[wiki links]]`，不锁用户
3. **自增强循环** — 问答沉淀 → 知识库变强 → 问答更准

---

## 四、技术架构

```
┌─────────────────────────────────────────────┐
│           Frontend (React + Vite)            │
│  Import / Library / Chat / Settings          │
└──────────────────┬──────────────────────────┘
                   │ REST API / SSE
┌──────────────────▼──────────────────────────┐
│          Backend (Python FastAPI)             │
│  Ingestion → Compilation → Q&A Engine        │
│  Parser │ LLM Client (LiteLLM) │ Indexer     │
└──────────────────┬──────────────────────────┘
                   │ File System I/O
┌──────────────────▼──────────────────────────┐
│        Obsidian Vault (本地文件夹)             │
│  .wiki/ │ raw/ │ wiki/ │ outputs/            │
└─────────────────────────────────────────────┘
```

数据存储：SQLite + FTS5 全文索引（Phase 2 计划加向量检索 SQLite-vec）

---

## 五、待完成事项

### Phase 3 实施开发（全部未完成）

- [ ] 后端核心业务逻辑（编译链路、问答链路、导入完整流程）
- [ ] 前端功能接通（与后端 API 对接）
- [ ] E2E 测试
- [ ] 部署方案（Docker）

### 官网与主项目串联

- [ ] 官网 → 应用入口的完整用户旅程
- [ ] 商业化闭环（注册、付费、License 验证）

---

## 六、风险与挑战

| 风险 | 说明 | 缓解 |
|------|------|------|
| 编译质量 | 核心价值依赖 LLM 编译质量，概念提取不准则飞轮断裂 | 充分的 Prompt 工程 + 人工反馈循环 |
| LLM 成本 | 每篇文档完整重写，token 消耗大 | 支持本地模型 + 缓存策略 |
| 竞品压力 | Readwise Reader AI、Mem.ai、Obsidian Copilot | 差异化在"编译"而非"索引" |
| 实施进度 | 设计完备但代码实施刚起步 | 聚焦 MVP 核心链路 |

---

## 七、关键决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 数据存储 | SQLite + 本地文件 | 本地优先，无需额外服务 |
| LLM 接口 | LiteLLM 统一封装 | 支持多模型，降低锁定 |
| 前端框架 | React + Vite | 轻量快速，社区成熟 |
| 官网框架 | Next.js | SEO + SSG 优势 |
| API 认证 | 用户名密码 + JWT | 本地应用安全需求 |
| 编译模式 | 混合同步/异步 | 小批量同步，大批量异步 |
| 测试策略 | VCR 录制回放 LLM 调用 | 零成本、确定性 |
