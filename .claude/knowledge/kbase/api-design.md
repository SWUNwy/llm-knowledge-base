# API 设计知识

> 本文档沉淀 LLM Knowledge Base 项目的 API 设计相关知识。

---

## 一、API 路由规范

### 路由结构

```
/api/v1/
├── auth/                    # 用户认证
│   ├── POST /setup          # 初始化设置（创建首个用户）
│   ├── POST /login          # 用户登录
│   └── GET /status          # 查询认证状态
├── ingest/                  # 文档导入
│   ├── POST /url            # 导入 URL
│   ├── POST /file           # 导入本地文件路径
│   ├── POST /video          # 导入视频 URL
│   ├── POST /github         # 导入 GitHub 仓库
│   └── GET /{id}/status     # 查询导入状态
├── documents/               # 文档管理
│   ├── GET /                # 文档列表（分页+搜索）
│   ├── GET /{id}            # 获取文档详情
│   ├── DELETE /{id}         # 删除文档
│   └── POST /search         # 全文搜索
├── compile/                 # 文档编译
│   ├── POST /               # 触发编译（sync/async）
│   └── GET /tasks/{task_id} # 查询编译任务状态
├── qa/                      # 知识问答
│   ├── POST /ask            # 提问（支持 SSE 流式）
│   └── GET /history         # QA 历史记录
├── concepts/                # 概念管理
│   ├── GET /                # 概念列表
│   └── GET /{id}            # 概念详情
├── settings/                # 系统设置
│   ├── GET /                # 获取设置
│   ├── PUT /                # 更新设置
│   └── POST /verify-llm     # 验证 LLM 配置
├── prompts/                 # Prompt 模板管理
│   ├── GET /                # 获取所有模板
│   ├── GET /{name}          # 获取指定模板
│   ├── PUT /{name}          # 自定义覆盖模板
│   └── DELETE /{name}       # 删除自定义覆盖
└── system/                  # 系统状态
    ├── GET /status          # 系统状态
    └── GET /stats           # 统计数据

/api/                        # 官网 API（website/ 项目）
├── auth/                    # 官网认证
│   ├── POST /register       # 用户注册
│   ├── POST /login          # 登录
│   └── POST /refresh        # 刷新 token
├── license/
│   ├── POST /verify         # 验证 License token
│   └── GET /status          # 查询 License 状态
├── llm/proxy                # LLM 代理（SSE 流式）
├── usage/current            # 当前使用量
└── stripe/
    ├── POST /checkout       # 创建 Stripe Checkout 会话
    └── POST /webhook        # Stripe Webhook

/health                      # 健康检查
```

### HTTP 方法映射

| 方法 | 用途 |
|------|------|
| GET | 获取资源（列表/详情/状态） |
| POST | 创建资源（导入/编译/提问/登录） |
| PUT | 更新资源（设置/模板覆盖） |
| DELETE | 删除资源 |

## 二、请求响应规范

### 字段转换规则
- **数据库字段** → snake_case
- **API 请求字段** → snake_case
- **API 响应字段** → snake_case
- **转换位置**：无转换（数据库字段 = API 字段 = snake_case）

### 成功响应格式

```json
// GET /api/v1/documents
{
  "total": 42,
  "page": 1,
  "limit": 20,
  "items": [
    {
      "id": "doc-abc123",
      "title": "机器学习入门",
      "type": "web",
      "status": "processed",
      "created_at": "2026-04-09T10:00:00",
      "tags": ["AI", "ML"]
    }
  ]
}

// POST /api/v1/compile (sync)
{
  "id": "comp-abc123",
  "title": "编译后的Wiki文章标题",
  "content": "# 编译结果\n\nMarkdown 内容...",
  "path": "/wiki/compiled/doc-abc123.md",
  "task_id": null
}

// POST /api/v1/compile (async, >5 docs)
{
  "task_id": "compile-abc123def456"
}
```

### 错误响应格式

```json
// 统一错误响应
{
  "error": {
    "code": "LLM_API_KEY_INVALID",
    "message": "LLM API Key authentication failed"
  }
}
```

## 三、错误处理

### 错误代码体系

```
ErrorCode 枚举（backend/src/errors.py）:

LLM 相关:
  LLM_API_KEY_INVALID    — API Key 认证失败
  LLM_QUOTA_EXCEEDED     — 配额超限
  LLM_RATE_LIMIT         — 速率限制
  LLM_TIMEOUT            — 请求超时
  LLM_SERVICE_DOWN       — 服务不可用
  LLM_MODEL_NOT_FOUND    — 模型不存在

导入相关:
  IMPORT_INVALID_URL     — URL 无效或不可达
  IMPORT_FILE_NOT_FOUND  — 文件未找到
  IMPORT_PARSE_FAILED    — 内容解析失败

认证相关:
  AUTH_INVALID_CREDENTIALS — 用户名或密码错误
  AUTH_TOKEN_EXPIRED       — Token 过期
  AUTH_SETUP_REQUIRED      — 需要初始化设置

通用:
  NOT_FOUND              — 资源不存在
  VALIDATION_ERROR       — 参数验证失败
  INTERNAL_ERROR         — 服务器内部错误
```

### HTTP 状态码使用

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| 200 | 成功 | 请求成功处理 |
| 201 | 创建成功 | 资源创建成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未认证 | 未登录或 token 过期 |
| 404 | 未找到 | 资源不存在 |
| 422 | 参数错误 | 请求体验证失败 |
| 429 | 速率限制 | 请求过频 |
| 500 | 服务器错误 | 内部错误 |

### 实现机制

1. 后端抛出 `AppError(code, detail, status_code)`
2. `error_handler.py` 中的 FastAPI exception_handler 捕获
3. 转换为统一 JSON 格式
4. 前端 `api.ts` 中的 `ApiError` 类重新包装
5. 前端组件通过 `ErrorAlert` 组件展示给用户

## 四、认证机制

### 请求认证

```
Authorization: Bearer <jwt_token>

// Cloud 模式额外头部
X-License-Token: <license_token>
```

### Token 规范

- **算法**: HS256
- **过期**: 24 小时
- **存储**: 前端 localStorage，key 为 `llm_kb_token`
- **密钥**: `app_secret_key`（环境变量）

### 双认证模式

| 模式 | 适用场景 | 认证方式 | Token 来源 |
|------|---------|---------|-----------|
| local | 个人自托管 | JWT（本地签发） | POST /api/v1/auth/login |
| cloud | SaaS 付费用户 | JWT + License Token | Cloud API login |

---

*由 Project Knowledge 于 2026-05-26 自动生成*
