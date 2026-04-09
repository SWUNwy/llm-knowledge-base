# R002 - 任务清单

## Phase 1: 后端基础设施

- [ ] T1.1 创建 `backend/src/errors.py`
  - 定义 `ErrorCode` 枚举（LLM / 导入 / 认证 / 通用 四大类）
  - 定义 `AppError` 自定义异常类
- [ ] T1.2 创建 `backend/src/middleware/error_handler.py`
  - 实现 `AppError` 异常处理器
  - 实现 `HTTPException` 转换处理器
  - 实现通用 `Exception` 兜底处理器
- [ ] T1.3 修改 `backend/src/main.py`
  - 注册全局异常处理器
- [ ] T1.4 修改 `backend/src/llm/client.py`
  - `generate()` 方法：将 litellm 异常转换为 `AppError`
  - `stream()` 方法：同样转换异常
- [ ] T1.5 修改 `backend/src/routers/qa.py`
  - `ask_question()`: 移除 `detail=f"...{e}"` 直接暴露异常
  - `_stream_response()`: 使用 AppError

## Phase 2: 前端基础设施

- [ ] T2.1 创建 `frontend/src/lib/errorMessages.ts`
  - 定义 `ErrorMessage` 类型
  - 实现 `ERROR_MESSAGES` 映射表（覆盖所有 ErrorCode）
  - 导出 `getErrorMessage(code: string): ErrorMessage` 函数
- [ ] T2.2 创建 `frontend/src/components/ErrorAlert.tsx`
  - 实现 inline / card / toast 三种展示形态
  - 支持传入 `ApiError` 或 `Error` 对象
  - 包含建议文本和快捷操作按钮
- [ ] T2.3 修改 `frontend/src/services/api.ts`
  - 定义 `ApiError` 类（包含 code、message、status）
  - 修改 `request()` 方法解析后端统一错误格式
  - 兼容旧格式（无 code 字段时降级处理）

## Phase 3: 页面改造

- [ ] T3.1 改造 `frontend/src/pages/Chat.tsx`
  - `onError` 回调使用 `ErrorAlert`（card variant）
  - 添加「重新提问」按钮
- [ ] T3.2 改造 `frontend/src/pages/Import.tsx`
  - 四个导入表单的错误提示替换为 `ErrorAlert`（inline variant）
- [ ] T3.3 改造 `frontend/src/pages/Library.tsx`
  - 错误展示替换为 `ErrorAlert`（card variant）
  - 添加「重新加载」按钮
- [ ] T3.4 改造 `frontend/src/pages/Settings.tsx`
  - 连接测试错误替换为 `ErrorAlert`（inline variant）
- [ ] T3.5 改造 `frontend/src/pages/Login.tsx`
  - 登录错误替换为友好消息
  - 特殊处理 `AUTH_SETUP_REQUIRED` 错误码

## Phase 4: 验证

- [ ] T4.1 手动验证所有错误场景
- [ ] T4.2 代码审查
