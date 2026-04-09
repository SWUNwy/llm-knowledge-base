# R002 - 错误处理 UX 优化

## 背景

当前系统在错误发生时，会直接将技术性错误信息展示给用户。例如在 Chat 页面发送消息后，如果 LLM API Key 无效，用户会看到：

```
Error: Failed to generate answer: litellm.AuthenticationError: GeminiException - {
  "error": {
    "code": 400,
    "message": "API key not valid. Please pass a valid API key."
    ...
  }
}
```

这种展示方式存在严重的用户体验问题：
1. 暴露内部实现细节（litellm、GeminiException）
2. JSON 格式对普通用户不友好
3. 没有提供解决建议
4. 长文本占据大量屏幕空间

## 目标

1. **友好消息**：用户看到简洁、易懂的错误标题和描述
2. **可操作性**：每种错误附带解决建议或快捷操作入口
3. **一致性**：全系统统一错误展示风格
4. **可维护性**：错误码集中管理，前后端共享

## 范围

### 包含

- 后端错误码体系（ErrorCode 枚举 + 自定义异常）
- 后端全局异常处理器（统一错误响应格式）
- 前端错误消息映射（ErrorCode → 友好消息）
- 前端统一错误展示组件（ErrorAlert）
- Chat / Import / Library / Settings / Login 页面错误处理改造
- LLM 相关错误的特殊处理（API Key、配额、限流等）

### 不包含

- 国际化（i18n）支持（后续 Phase 2）
- 错误日志上报/监控
- 后端路由级别的细粒度权限错误

## 影响范围

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `backend/src/errors.py` | 新增 | 错误码 + 自定义异常 |
| `backend/src/middleware/error_handler.py` | 新增 | 全局异常处理器 |
| `backend/src/main.py` | 修改 | 注册异常处理器 |
| `backend/src/routers/qa.py` | 修改 | 使用新错误类型 |
| `backend/src/routers/ingest.py` | 修改 | 使用新错误类型 |
| `backend/src/llm/client.py` | 修改 | 转换 LLM 异常 |
| `frontend/src/lib/errorMessages.ts` | 新增 | 错误消息映射 |
| `frontend/src/components/ErrorAlert.tsx` | 新增 | 统一错误展示组件 |
| `frontend/src/services/api.ts` | 修改 | 错误响应解析 |
| `frontend/src/pages/Chat.tsx` | 修改 | 使用 ErrorAlert |
| `frontend/src/pages/Import.tsx` | 修改 | 使用 ErrorAlert |
| `frontend/src/pages/Library.tsx` | 修改 | 使用 ErrorAlert |
| `frontend/src/pages/Settings.tsx` | 修改 | 使用 ErrorAlert |
| `frontend/src/pages/Login.tsx` | 修改 | 使用 ErrorAlert |

## 成功标准

| 指标 | 目标 |
|------|------|
| 技术错误不再直接暴露给用户 | 100% |
| 每种错误都有对应的用户友好消息 | 100% |
| 关键错误附带解决建议 | LLM 相关 100%，通用 ≥ 80% |
| 错误展示风格统一 | 全页面一致 |

## 关键决策记录

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 错误码方案 | 字符串枚举 | 可读性好，前后端一致 |
| 错误映射位置 | 前端集中管理 | 减少后端变更范围，前端可灵活调整文案 |
| 后端错误转换 | 全局中间件 | 统一拦截，不侵入业务代码 |
