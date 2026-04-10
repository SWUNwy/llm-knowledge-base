# R002 - 任务清单

> 最后更新：2026-04-10
> 需求：错误处理 UX 优化
> 状态：基础设施已完成，页面改造部分完成

## Phase 1: 后端基础设施

- [x] T1.1 创建 `backend/src/errors.py`
  - ErrorCode 枚举已定义（LLM / 导入 / 认证 / 通用 四大类，15 个错误码）
  - AppError 自定义异常类已实现
  - DEFAULT_MESSAGES 映射表已定义
- [x] T1.2 创建 `backend/src/middleware/error_handler.py`
  - AppError 异常处理器已实现
  - RequestValidationError 处理器已实现
  - 通用 Exception 兜底处理器已实现
- [x] T1.3 修改 `backend/src/main.py`
  - 全局异常处理器已注册 (`register_error_handlers(app)`)
- [x] T1.4 修改 `backend/src/llm/client.py`
  - `generate()` 方法：已将 litellm 异常转换为 AppError（AuthenticationError → LLM_API_KEY_INVALID, RateLimitError → LLM_RATE_LIMIT, Timeout → LLM_TIMEOUT 等）
  - `stream()` 方法：同样已转换异常
- [x] T1.5 修改 `backend/src/routers/qa.py`
  - 已使用 AppError 进行异常处理
  - 已导入 ErrorCode

## Phase 2: 前端基础设施

- [x] T2.1 创建 `frontend/src/lib/errorMessages.ts`
  - ErrorMessage 类型已定义
  - ERROR_MESSAGES 映射表已覆盖所有 ErrorCode（15 个）
  - `getErrorMessage(code)` 函数已导出
- [x] T2.2 创建 `frontend/src/components/ErrorAlert.tsx`
  - inline / card / toast 三种展示形态
  - 支持 ApiError 和 Error 对象
  - 包含建议文本和快捷操作按钮
- [x] T2.3 修改 `frontend/src/services/api.ts`
  - ApiError 类已定义（包含 code、message、status）
  - request() 方法已解析后端统一错误格式
  - 兼容旧格式

## Phase 3: 页面改造

- [x] T3.1 改造 `frontend/src/pages/Chat.tsx`
  - 已使用 ErrorAlert 组件
  - 已添加「重新提问」按钮
- [x] T3.2 改造 `frontend/src/pages/Import.tsx`
  - 已使用 ErrorAlert 组件
- [x] T3.3 改造 `frontend/src/pages/Library.tsx`
  - 已使用 ErrorAlert 组件
  - 已添加「重新加载」按钮
- [x] T3.4 改造 `frontend/src/pages/Settings.tsx`
  - 已使用 ErrorAlert 组件
- [x] T3.5 改造 `frontend/src/pages/Login.tsx`
  - 已使用友好错误消息
  - 已处理 AUTH_SETUP_REQUIRED 错误码

## Phase 4: 验证

- [ ] T4.1 手动验证所有错误场景
- [ ] T4.2 代码审查

## 实现统计

| 组件 | 代码行数 | 状态 |
|------|---------|------|
| backend/src/errors.py | 82 行 | 完成 |
| backend/src/middleware/error_handler.py | 57 行 | 完成 |
| backend/src/llm/client.py（错误转换） | ~20 行 | 完成 |
| frontend/src/lib/errorMessages.ts | 97 行 | 完成 |
| frontend/src/components/ErrorAlert.tsx | 128 行 | 完成 |
| frontend/src/services/api.ts（ApiError） | ~15 行 | 完成 |

## 备注

- 错误处理基础设施已在开发过程中提前实现，不需要单独一轮改造
- 所有 15 个 ErrorCode 均已在前后端实现
- 剩余工作：手动验证所有错误场景 + 代码审查
