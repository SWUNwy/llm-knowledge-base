# R002 - 测试用例

## 测试策略

1. **单元测试**：后端错误转换逻辑、前端错误消息映射
2. **集成测试**：API 错误响应格式验证
3. **E2E 测试**：用户可见的错误展示效果

## 后端测试用例

### TC-BK-01: AppError 异常处理器

| 场景 | 输入 | 预期输出 |
|------|------|---------|
| 正常处理 | `AppError(ErrorCode.LLM_API_KEY_INVALID)` | 500 响应，body 含 `error.code = "LLM_API_KEY_INVALID"` |
| 无 detail | `AppError(ErrorCode.NOT_FOUND)` | 不泄露内部信息 |

### TC-BK-02: LLM 异常转换

| 场景 | litellm 异常 | 预期 ErrorCode |
|------|-------------|---------------|
| API Key 无效 | `AuthenticationError` | `LLM_API_KEY_INVALID` |
| 限流 | `RateLimitError` | `LLM_RATE_LIMIT` |
| 超时 | `Timeout` | `LLM_TIMEOUT` |
| 服务不可用 | `APIConnectionError` | `LLM_SERVICE_DOWN` |
| 模型不存在 | `NotFoundError` | `LLM_MODEL_NOT_FOUND` |
| 其他异常 | `Exception("unknown")` | `INTERNAL_ERROR` |

### TC-BK-03: 通用异常兜底

| 场景 | 输入 | 预期行为 |
|------|------|---------|
| 未捕获异常 | `ValueError("something")` | 返回 INTERNAL_ERROR，记录完整堆栈 |

## 前端测试用例

### TC-FE-01: 错误消息映射

| 场景 | ErrorCode | 预期结果 |
|------|-----------|---------|
| LLM API Key 无效 | `LLM_API_KEY_INVALID` | 返回包含 title 和 suggestion 的对象 |
| 未知错误码 | `UNKNOWN_ERROR` | 返回通用友好消息 |

### TC-FE-02: ApiError 解析

| 场景 | 后端响应 | 预期行为 |
|------|---------|---------|
| 新格式 | `{ error: { code, message } }` | 抛出 `ApiError(code, message)` |
| 旧格式兼容 | `{ detail: "old error" }` | 抛出 `ApiError(null, "old error")` |

## E2E 测试用例

### TC-E2E-01: Chat 页面 LLM 错误展示

**前置条件**：
- 已登录用户
- LLM API Key 配置为无效值

**步骤**：
1. 访问 `/chat` 页面
2. 输入任意问题并发送

**预期结果**：
- 不显示原始 litellm 错误信息
- 显示友好的错误提示，包含「API Key 无效」
- 显示「请前往设置页面配置 API Key」建议
- 不显示技术细节（GeminiException、JSON 等）

### TC-E2E-02: Chat 页面重试功能

**步骤**：
1. 在错误状态下点击「重新提问」按钮

**预期结果**：
- 按钮可点击，重新发起请求
- 若成功，显示正常回复

### TC-E2E-03: Import 页面 URL 导入错误

**步骤**：
1. 在 Import 页面输入无效 URL（如 `not-a-url`）
2. 点击「Import URL」

**预期结果**：
- 显示 `ErrorAlert` 组件（inline variant）
- 显示友好错误描述，不显示技术栈

### TC-E2E-04: Login 页面认证错误

**前置条件**：
- 系统已初始化，有用户

**步骤**：
1. 输入错误的用户名/密码
2. 点击「Sign in」

**预期结果**：
- 显示「用户名或密码错误」
- 不显示后端堆栈或 JWT 相关错误

## 错误场景清单

| 编号 | 场景 | ErrorCode | 优先级 |
|------|------|-----------|-------|
| E001 | LLM API Key 无效 | `LLM_API_KEY_INVALID` | P0 |
| E002 | LLM 配额用完 | `LLM_QUOTA_EXCEEDED` | P1 |
| E003 | LLM 限流 | `LLM_RATE_LIMIT` | P1 |
| E004 | LLM 超时 | `LLM_TIMEOUT` | P1 |
| E005 | LLM 服务不可用 | `LLM_SERVICE_DOWN` | P1 |
| E006 | LLM 模型不存在 | `LLM_MODEL_NOT_FOUND` | P2 |
| E007 | 导入 URL 无效 | `IMPORT_INVALID_URL` | P1 |
| E008 | 导入文件不存在 | `IMPORT_FILE_NOT_FOUND` | P1 |
| E009 | 导入解析失败 | `IMPORT_PARSE_FAILED` | P2 |
| E010 | 用户名密码错误 | `AUTH_INVALID_CREDENTIALS` | P0 |
| E011 | Token 过期 | `AUTH_TOKEN_EXPIRED` | P1 |
| E012 | 系统未初始化 | `AUTH_SETUP_REQUIRED` | P0 |
| E013 | 资源不存在 | `NOT_FOUND` | P2 |
| E014 | 参数校验失败 | `VALIDATION_ERROR` | P2 |
| E015 | 未知错误 | `INTERNAL_ERROR` | P0 |
