# R003 - 测试用例

## 用户注册与登录

### TC-R003-001: 新用户注册

- 前置：无账号
- 步骤：
  1. 访问 /register
  2. 输入邮箱 + 密码
  3. 提交注册
  4. 跳转 Stripe Checkout
  5. 完成支付（14 天试用）
  6. 跳转 /dashboard
- 预期：
  - users 表创建记录
  - subscriptions 表创建记录，status=trialing，tier=trial
  - Dashboard 显示"试用中"，到期时间 14 天后

### TC-R003-002: 已有用户登录

- 前置：已有账号
- 步骤：
  1. 访问 /login
  2. 输入邮箱 + 密码
  3. 提交登录
- 预期：
  - 返回 JWT
  - 跳转 /dashboard

### TC-R003-003: 本地应用登录

- 前置：已有账号
- 步骤：
  1. 启动本地应用
  2. 输入邮箱 + 密码
  3. 提交
- 预期：
  - POST /api/auth/login 成功
  - 返回 License Token
  - Token 缓存到本地
  - 进入主界面

### TC-R003-004: 错误密码登录

- 前置：已有账号
- 步骤：输入错误密码提交
- 预期：返回 401，提示密码错误

## License 验证

### TC-R003-010: 有效 License 启动

- 前置：本地有缓存 token，订阅有效
- 步骤：启动应用
- 预期：验证通过，加载 limits，进入主界面

### TC-R003-011: 过期 License 启动

- 前置：本地有缓存 token，订阅已到期
- 步骤：启动应用
- 预期：验证失败，清除缓存，显示登录页

### TC-R003-012: 离线启动

- 前置：本地有缓存 token，无网络
- 步骤：启动应用（断网状态）
- 预期：使用缓存 limits，允许使用（24h 内）

### TC-R003-013: 无 License 启动

- 前置：首次安装，无缓存 token
- 步骤：启动应用
- 预期：显示登录页

## Stripe 支付

### TC-R003-020: 新用户付费流程

- 前置：已注册，处于试用状态
- 步骤：
  1. Dashboard 点击"升级到专业版"
  2. 跳转 Stripe Checkout
  3. 完成支付
- 预期：
  - Webhook 收到 checkout.session.completed
  - subscriptions 表更新 tier=professional
  - tier_limits 读取到专业版限额

### TC-R003-021: 自动续费成功

- 前置：月付订阅到期
- 步骤：Stripe 自动扣款成功
- 预期：
  - Webhook 收到 invoice.payment_succeeded
  - period_end 延长一个月
  - 月用量重置

### TC-R003-022: 续费失败

- 前置：月付订阅到期，扣款失败
- 步骤：Stripe 扣款失败
- 预期：
  - Webhook 收到 invoice.payment_failed
  - status 标记为 past_due
  - 用户下次启动应用时收到提示

### TC-R003-023: 用户取消订阅

- 前置：有效订阅
- 步骤：Dashboard → 取消订阅 → Stripe Customer Portal
- 预期：
  - cancel_at_period_end=true
  - 当前周期结束后 tier 降为 free
  - License token 失效

## LLM Proxy

### TC-R003-030: 编译请求（额度内）

- 前置：专业版用户，当月编译 0 次
- 步骤：导入一篇文档，触发编译
- 预期：
  - Cloud API 验证 token 通过
  - 检查限额：0 < unlimited，放行
  - 转发给 LLM，流式返回结果
  - usage_logs 记录一条 compile 日志
  - 本地应用写入 wiki/*.md

### TC-R003-031: 编译请求（超额度）

- 前置：个人版用户，当月编译已达 30 次
- 步骤：触发编译
- 预期：
  - Cloud API 返回 429
  - 本地应用提示"本月编译次数已用完，请升级"
  - usage_logs 不记录（未执行）

### TC-R003-032: 问答请求

- 前置：专业版用户
- 步骤：用户提问，本地 FTS 检索到 3 个片段，发送给 Cloud API
- 预期：
  - 只发送检索到的片段，非全文
  - 流式返回回答
  - 本地显示回答 + 来源引用

### TC-R003-034: 无效 Token 的 LLM 请求

- 前置：Token 过期或伪造
- 步骤：发送 LLM proxy 请求
- 预期：返回 401 Unauthorized

## Tier Limits 可配置

### TC-R003-040: 运营调整限额

- 前置：个人版编译限额 30 次/月
- 步骤：
  1. UPDATE tier_limits SET max_compiles=50 WHERE tier='personal'
  2. 用户触发编译
- 预期：新限额立即生效，无需重新部署
