# R003 - 任务清单

## Phase 2: Website 升级 + Cloud API

### 2.1 基础设施

- [ ] 配置 PostgreSQL 数据库（Supabase 或 Neon）
- [ ] 创建数据库 schema（users, subscriptions, license_tokens, usage_logs, tier_limits, releases）
- [ ] 配置 Stripe 账号，创建 Products & Prices（个人版/专业版/团队版，月付/年付）
- [ ] 配置环境变量（DATABASE_URL, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, JWT_SECRET）

### 2.2 用户系统

- [ ] 实现 /register 页面（邮箱 + 密码）
- [ ] 实现 /login 页面（替换现有占位页）
- [ ] 实现 POST /api/auth/register（注册 API）
- [ ] 实现 POST /api/auth/login（登录 API，返回 JWT + License Token）
- [ ] 实现 POST /api/auth/refresh（Token 刷新）

### 2.3 Stripe 集成

- [ ] 实现 POST /api/stripe/checkout（创建 Checkout Session）
- [ ] 实现 POST /api/stripe/webhook（Webhook 处理）
  - [ ] checkout.session.completed
  - [ ] customer.subscription.updated
  - [ ] customer.subscription.deleted
  - [ ] invoice.payment_succeeded
  - [ ] invoice.payment_failed
- [ ] 集成 Stripe Customer Portal（降级/取消/账单历史）

### 2.4 Dashboard

- [ ] 实现 /dashboard 页面（套餐状态、用量图表、下载入口）
- [ ] 实现 /dashboard/billing 页面（Stripe Portal 跳转）
- [ ] 实现下载安装包功能（从 releases 表读取版本和链接）

### 2.5 Cloud API

- [ ] 实现 POST /api/license/verify（License 验证）
- [ ] 实现 GET /api/license/status（License 状态查询）
- [ ] 实现 POST /api/llm/proxy（LLM 请求代理）
  - [ ] Token 验证
  - [ ] 限额检查（读 tier_limits + usage_logs）
  - [ ] 模型选择（按 tier 路由）
  - [ ] SSE 流式转发
  - [ ] 用量记录
- [ ] 实现 GET /api/usage/current（当月用量查询）

### 2.6 落地页调整

- [ ] Pricing 按钮 → Stripe Checkout（登录后）/ 注册页（未登录）
- [ ] CTA 按钮 → 注册页或 Dashboard（已登录）
- [ ] Navbar 登录状态展示

## Phase 3: 本地应用改造

### 3.1 License 模块

- [ ] 新增 license/manager.py（License 缓存、验证、刷新）
- [ ] 新增 license/limits.py（本地 limits 缓存 + 用量追踪）
- [ ] 新增 auth/cloud_auth.py（Cloud API 认证客户端）
- [ ] 修改 config.py（新增 CLOUD_API_URL 配置）

### 3.2 启动流程改造

- [ ] 应用启动时检查 cached_license_token
- [ ] 启动时调用 Cloud API 验证 License
- [ ] 验证失败 → 显示登录页
- [ ] 网络错误 → 使用缓存 limits，允许离线 24h
- [ ] 后台每 6h 异步刷新 token

### 3.3 LLM 调用改造

- [ ] 新增 CloudLLMClient（调用 /api/llm/proxy）
- [ ] 编译流程改为走 Cloud 代理
- [ ] 问答流程改为走 Cloud 代理
- [ ] 保留直连模式作为降级方案（用户配了 API Key 时）

### 3.4 前端改造

- [ ] Login 页面改造：邮箱 + 密码 → Cloud API
- [ ] Login 页面增加"注册"链接（打开浏览器）
- [ ] 删除 Setup 页面
- [ ] Settings 页面改造：展示套餐、用量、可用模型
- [ ] 编译/问答按钮旁显示剩余次数
- [ ] 401 响应时自动跳转登录页

## Phase 4: 测试与上线

### 4.1 后端测试

- [ ] Cloud API 单元测试（auth, license, llm-proxy, usage）
- [ ] Stripe Webhook 集成测试（使用 Stripe CLI 模拟事件）
- [ ] 数据库迁移测试

### 4.2 前端测试

- [ ] Website E2E 测试（注册→付费→Dashboard 流程）
- [ ] 本地应用 License 验证流程测试

### 4.3 部署

- [ ] Vercel 部署 Website + Cloud API
- [ ] 数据库 migration 上线
- [ ] Stripe Webhook endpoint 配置（生产环境）
- [ ] DNS 配置（knowledgebase.ai）
- [ ] SSL 证书（Vercel 自动）
