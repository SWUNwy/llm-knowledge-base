# 术语映射表

> 解决业务 ↔ 代码 ↔ API 的命名脱节问题。

---

## 实体术语映射

| 业务术语 | 英文术语 | 代码命名 | API 路径 | 数据库表 |
|---------|---------|---------|---------|---------|
| 文档 | Document | `Document` | `/api/v1/documents` | `documents` |
| 概念 | Concept | `Concept` | `/api/v1/concepts` | `concepts` |
| 用户 | User | `User` | `/api/v1/auth` | `users` |
| 文档链接 | Link | `Link` | — | `links` |
| 编译任务 | Compile Task | `CompileTask` | `/api/v1/compile/tasks` | `compile_tasks` |
| QA 记录 | QA History | `QAHistory` | `/api/v1/qa/history` | `qa_history` |
| 文档-概念关联 | Doc-Concept | `DocConcept` | — | `doc_concepts` |
| 订阅 | Subscription | `Subscription` | —（website） | `subscriptions` |
| 许可证令牌 | License Token | `LicenseToken` | `/api/license` | `license_tokens` |
| 使用日志 | Usage Log | `UsageLog` | `/api/usage` | `usage_logs` |
| 层级限制 | Tier Limit | `TierLimits` | — | `tier_limits` |
| 发布版本 | Release | `Release` | — | `releases` |

## 字段术语映射

| 业务术语 | 英文术语 | 数据库字段 | API 字段 | TypeScript/Python 类型 |
|---------|---------|-----------|---------|----------------------|
| 文档 ID | Document ID | `id` | `id` | `str` |
| 文档类型 | Document Type | `type` | `type` | `DocumentType` (enum) |
| 文档路径 | Document Path | `path` | `path` | `str` |
| 文档标题 | Title | `title` | `title` | `str` |
| 文档状态 | Status | `status` | `status` | `DocumentStatus` (enum) |
| 创建时间 | Created At | `created_at` | `created_at` | `datetime` |
| 更新时间 | Updated At | `updated_at` | `updated_at` | `datetime` |
| 元数据 | Metadata | `metadata` | `metadata` | `dict` |
| 概念名称 | Concept Name | `name` | `name` | `str` |
| Wiki 路径 | Wiki Path | `wiki_path` | `wiki_path` | `str` |
| 提及次数 | Mention Count | `mention_count` | `mention_count` | `int` |
| 相关性分数 | Relevance Score | `relevance_score` | `relevance_score` | `float` |
| 来源 URL | Source URL | `source_url` | `source_url` | `Optional[str]` |
| 标签 | Tags | `tags` | `tags` | `list[str]` |
| 用户名 | Username | `username` | `username` | `str` |
| 密码哈希 | Password Hash | `password_hash` | `password_hash` | `str` |

## 状态术语映射

| 业务术语 | 英文术语 | 数据库值 | 说明 |
|---------|---------|---------|------|
| 待处理 | Pending | `pending` | 文档刚导入，尚未处理 |
| 已处理 | Processed | `processed` | 文档已编译完成 |
| 待编译 | Pending | `pending` | 编译任务等待执行 |
| 编译中 | Running | `running` | 编译任务进行中 |
| 已完成 | Completed | `completed` | 编译任务完成 |
| 已失败 | Failed | `failed` | 编译任务失败 |
| 活跃 | Active | `active` | 订阅活跃中 |
| 已取消 | Canceled | `canceled` | 订阅已取消 |
| 逾期 | Past Due | `past_due` | 支付失败 |
| 试用中 | Trialing | `trialing` | 免费试用期 |
| 显式链接 | Explicit | `explicit` | 用户明确创建的链接 |
| 隐式链接 | Implicit | `implicit` | 系统自动推断的链接 |

## 文档类型映射

| 业务术语 | 英文术语 | 数据库值 | 说明 |
|---------|---------|---------|------|
| 网页 | Web | `web` | URL/HTML 来源 |
| 论文 | Paper | `paper` | PDF 学术论文 |
| 视频 | Video | `video` | YouTube/Bilibili 视频 |
| 代码 | Code | `code` | GitHub 仓库源代码 |

## 易混淆术语

| ❌ 错误用法 | ✅ 正确用法 | 说明 |
|------------|------------|------|
| vault_path / vault | `VAULT_PATH` | 环境变量名使用 SCREAMING_SNAKE_CASE |
| secret | `app_secret_key` | JWT 签名密钥，非 OpenAI 的 API Key |
| document type / doc_type | `type` | 使用 type 字段，值见文档类型映射表 |

## API 路由映射

| 用途 | API 路径 | 前端文件 | 后端文件 |
|------|---------|---------|---------|
| 用户注册/登录 | `/api/v1/auth/*` | `Login.tsx` | `routers/auth.py` |
| 文档导入 | `/api/v1/ingest/*` | `Import.tsx` | `routers/ingest.py` |
| 文档管理 | `/api/v1/documents/*` | `Library.tsx` | `routers/documents.py` |
| 编译 | `/api/v1/compile/*` | `Library.tsx` | `routers/compile.py` |
| 问答 | `/api/v1/qa/*` | `Chat.tsx` | `routers/qa.py` |
| 概念管理 | `/api/v1/concepts/*` | `Concepts.tsx` | `routers/concepts.py` |
| 设置 | `/api/v1/settings/*` | `Settings.tsx` | `routers/settings.py` |
| Prompt 管理 | `/api/v1/prompts/*` | — | `routers/prompts.py` |
| 系统状态 | `/api/v1/system/*` | — | `routers/system.py` |
| 健康检查 | `/health` | — | `main.py` |

## 新术语添加规范

当引入新业务概念时，按以下步骤添加：

1. **确定业务术语**：与用户确认中文名称
2. **确定英文术语**：使用单数形式
3. **确定代码命名**：
   - Python: PascalCase 类名, snake_case 字段
   - TypeScript: PascalCase 接口/类型, camelCase 变量
4. **确定 API 路径**：使用 kebab-case 复数形式，挂载在 `/api/v1/` 下
5. **确定数据库表名**：snake_case 复数
6. **更新本文件**：添加到对应映射表

---

*由 Project Knowledge 于 2026-05-26 自动生成*
