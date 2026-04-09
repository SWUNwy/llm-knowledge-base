# R002 - 错误处理 UX 优化 - 技术设计

## 1. 整体架构

```
[用户操作] → [前端 API] → [后端 Router] → [业务逻辑/LLM]
                  ↑                              |
                  |        统一错误响应            ↓
              [错误解析] ← [全局异常处理器] ← [异常抛出]
                  |
                  ↓
           [ErrorAlert 组件] → 用户看到友好提示
```

## 2. 后端设计

### 2.1 错误码定义 (`backend/src/errors.py`)

```python
class ErrorCode(str, Enum):
    # LLM 相关
    LLM_API_KEY_INVALID = "LLM_API_KEY_INVALID"
    LLM_QUOTA_EXCEEDED = "LLM_QUOTA_EXCEEDED"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_SERVICE_DOWN = "LLM_SERVICE_DOWN"
    LLM_MODEL_NOT_FOUND = "LLM_MODEL_NOT_FOUND"

    # 导入相关
    IMPORT_INVALID_URL = "IMPORT_INVALID_URL"
    IMPORT_FILE_NOT_FOUND = "IMPORT_FILE_NOT_FOUND"
    IMPORT_PARSE_FAILED = "IMPORT_PARSE_FAILED"

    # 认证相关
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_SETUP_REQUIRED = "AUTH_SETUP_REQUIRED"

    # 通用
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
```

### 2.2 自定义异常

```python
class AppError(Exception):
    def __init__(self, code: ErrorCode, detail: str = "", status_code: int = 500):
        self.code = code
        self.detail = detail  # 内部日志用，不暴露给用户
        self.status_code = status_code
```

### 2.3 统一错误响应格式

```json
{
  "error": {
    "code": "LLM_API_KEY_INVALID",
    "message": "API Key 认证失败，请检查 LLM 配置",
    "status": 500
  }
}
```

- `code` — 错误码，前端根据此码映射友好消息
- `message` — 后端提供的通用描述（前端可覆盖）
- 不包含 `detail`（防止泄露内部信息）

### 2.4 全局异常处理器

在 FastAPI 中注册 `@app.exception_handler`，拦截三类异常：

1. **`AppError`** — 业务异常，直接使用其 code 和 status_code
2. **`HTTPException`** — 转换为统一格式（兼容现有代码）
3. **`Exception`** — 兜底处理，返回 INTERNAL_ERROR，日志记录完整堆栈

### 2.5 LLM 异常转换

在 `llm/client.py` 中将 litellm 异常映射为 `AppError`：

| litellm 异常 | ErrorCode | HTTP Status |
|-------------|-----------|-------------|
| `AuthenticationError` | `LLM_API_KEY_INVALID` | 500 |
| `RateLimitError` | `LLM_RATE_LIMIT` | 429 |
| `Timeout` | `LLM_TIMEOUT` | 504 |
| `APIConnectionError` | `LLM_SERVICE_DOWN` | 502 |
| `NotFoundError` | `LLM_MODEL_NOT_FOUND` | 404 |
| 其他 `Exception` | `INTERNAL_ERROR` | 500 |

## 3. 前端设计

### 3.1 错误消息映射 (`frontend/src/lib/errorMessages.ts`)

```typescript
interface ErrorMessage {
  title: string;           // 简短标题
  description: string;     // 一句话描述
  suggestion?: string;     // 解决建议
  action?: {               // 快捷操作
    label: string;
    link: string;
  };
}
```

每种 ErrorCode 对应一个 `ErrorMessage`，示例：

| ErrorCode | title | description | suggestion |
|-----------|-------|-------------|------------|
| `LLM_API_KEY_INVALID` | API Key 无效 | LLM 服务认证失败 | 请在设置页面检查 API Key 配置 |
| `LLM_RATE_LIMIT` | 请求过于频繁 | API 调用速率已达上限 | 请稍等片刻后重试 |
| `LLM_TIMEOUT` | 响应超时 | LLM 服务响应时间过长 | 请检查网络连接或稍后重试 |
| `IMPORT_INVALID_URL` | URL 无效 | 无法访问指定的网址 | 请确认网址是否正确且可访问 |

### 3.2 API 错误解析 (`frontend/src/services/api.ts`)

修改 `ApiService.request()` 方法：

1. 捕获后端返回的 `{ error: { code, message } }` 格式
2. 抛出自定义 `ApiError` 对象，包含 `code` 和 `message`
3. 前端组件根据 `code` 查找友好消息

### 3.3 ErrorAlert 组件

```
┌──────────────────────────────────────────────────────┐
│ ⚠ {title}                                            │
│                                                      │
│ {description}                                        │
│                                                      │
│ 💡 {suggestion}            [{action.label} →]        │
└──────────────────────────────────────────────────────┘
```

Props：
- `error: ApiError | Error` — 错误对象
- `variant?: 'inline' | 'card' | 'toast'` — 展示形态
- `onDismiss?: () => void` — 关闭回调

支持的展示形态：
- `inline`：内联文本，用于表单下方的错误提示（Import、Login）
- `card`：卡片样式，用于 Chat 消息中的错误展示
- `toast`：右上角通知，用于操作失败提醒

## 4. 各页面改造方案

### 4.1 Chat 页面

**现状**：`Error: ${err.message}` 直接作为聊天气泡内容

**改造后**：
- 错误消息不再作为普通聊天气泡
- 使用 `ErrorAlert` 组件（card variant）展示在对话区域
- 包含「重试」按钮

### 4.2 Import 页面

**现状**：`<p className="text-red-600">{error.message}</p>`

**改造后**：
- 替换为 `<ErrorAlert variant="inline" />`
- 显示友好错误标题 + 建议

### 4.3 Library 页面

**现状**：红色错误框显示 `error.message`

**改造后**：
- 替换为 `<ErrorAlert variant="card" />`
- 附带「重试加载」按钮

### 4.4 Settings 页面

**现状**：连接测试失败显示 `error.message`

**改造后**：
- 替换为 `<ErrorAlert variant="inline" />`
- 针对不同错误提供具体建议

### 4.5 Login 页面

**现状**：登录失败显示 `error.message`

**改造后**：
- 保持现有错误框样式，但使用友好消息
- 特殊处理 `AUTH_SETUP_REQUIRED`，自动跳转到 Setup 页面
