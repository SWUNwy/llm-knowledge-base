# LLM Knowledge Base

> 一个本地运行的 Web 应用，自动将零散资料编译成结构化的 Obsidian 知识库，并用 LLM 驱动问答和持续增强。

## 功能特性

- **智能导入** — 支持 URL、PDF、视频、GitHub 仓库等多种来源
- **自动编译** — LLM 自动生成带双向链接的 Wiki 文章
- **智能问答** — 对知识库提问，答案可沉淀回库
- **本地优先** — 所有数据在你的 Obsidian vault 中，完全掌控
- **多模型支持** — 支持 Gemini、Claude、GPT、本地模型

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + TailwindCSS |
| 后端 | Python 3.11+ + FastAPI |
| 数据库 | SQLite + FTS5 |
| LLM | LiteLLM (统一接口) |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+

### 安装步骤

```bash
# 1. 克隆项目
git clone <repo-url>
cd llm-knowledge-base

# 2. 运行初始化脚本
chmod +x scripts/*.sh
./scripts/setup.sh

# 3. 编辑 .env 文件，配置 API Key 和 Vault 路径
cp .env.example .env
vim .env

# 4. 启动开发服务器（需要两个终端）
```

### 启动开发服务器

**终端 1 - 后端：**
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

**终端 2 - 前端：**
```bash
cd frontend
npm run dev
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端应用 | http://localhost:5173 |
| API 文档 | http://localhost:8000/docs |
| API 文档 | http://localhost:8000/redoc |
| OpenAPI 规范 | docs/api.yaml |

## 项目结构

```
llm-knowledge-base/
├── backend/           # Python FastAPI 后端
│   ├── src/           # 源代码
│   └── tests/         # 测试
├── frontend/          # React 前端
│   └── src/           # 源代码
├── docs/              # 文档
│   ├── api.yaml       # OpenAPI 规范
│   ├── design.md      # 设计文档
│   ├── project-overview.md # 项目全景复盘
│   └── requirements/  # 需求文档（Spec SDD）
│       └── active/    # 进行中的需求
├── scripts/           # 工具脚本
├── .env.example       # 环境变量模板
└── README.md
```

## 配置说明

见 [.env.example](.env.example) 获取所有可配置项。

### 必填配置

| 配置项 | 说明 |
|--------|------|
| `APP_SECRET_KEY` | 应用密钥，用于 JWT 签名 |
| `VAULT_PATH` | Obsidian vault 的绝对路径 |
| 至少一个 LLM API Key | Gemini / OpenAI / Anthropic |

## 开发指南

### 运行测试

```bash
./scripts/test.sh
```

### 代码规范

```bash
# 后端
cd backend
source venv/bin/activate
black src tests
ruff check src tests
mypy src

# 前端
cd frontend
npm run lint -- --fix
```

### API 文档导出

```bash
./scripts/export-api.sh
```

## 文档

- [产品需求文档](docs/requirements/active/R001-llm-knowledge-base/proposal.md)
- [技术设计文档](docs/requirements/active/R001-llm-knowledge-base/design.md)
- [任务清单](docs/requirements/active/R001-llm-knowledge-base/tasks.md)
- [测试用例](docs/requirements/active/R001-llm-knowledge-base/test-cases.md)
- [项目全景复盘](docs/project-overview.md)
- [商业化串联设计](docs/requirements/active/R003-commercial-integration/proposal.md)

## 许可证

MIT
