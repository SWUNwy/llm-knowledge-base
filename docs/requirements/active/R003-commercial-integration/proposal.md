# R003 - Commercial Integration

> 创建日期：2026-04-09
> 状态：设计完成，待实施

## 背景

LLM Knowledge Base 的核心产品已完成设计和部分开发，官网（website/）也已完成 Phase 1 MVP。但两者尚未串联：官网是纯展示页，本地应用是独立工具。

为将项目转化为可商业化的 SaaS 产品，需要将官网、云端 API、本地应用三者打通，实现完整的用户旅程：注册→付费→使用→续费。

## 目标

1. **Website 升级为 SaaS 入口**：增加用户系统、Stripe 付费、Dashboard、Cloud API
2. **本地应用改造成 SaaS 客户端**：License 验证、LLM 代理调用、用量展示
3. **完整的商业化闭环**：用户可从官网或应用注册，付费后下载使用，到期自动续费

## 范围

### 包含 (MVP)

- Website：注册/登录、Stripe Checkout + Webhook、Dashboard、Cloud API（auth/license/llm-proxy/usage）
- PostgreSQL 数据库：users, subscriptions, license_tokens, usage_logs, tier_limits
- 本地应用改造：登录对接 Cloud API、启动时 License 验证、LLM 调用改为走代理
- Stripe 集成：产品/价格配置、Checkout、Customer Portal、Webhook 处理

### 不包含 (Phase 2)

- 邮件发送系统（注册/续费通知）
- 团队版协作功能
- 高级分析功能

## 成功标准

| 指标 | 目标 |
|------|------|
| 注册→付费转化率 | ≥ 15%（试用 14 天后） |
| License 验证成功率 | ≥ 99%（正常网络环境） |
| LLM 代理响应时间 | 首字输出 < 2s |
| 付费用户月流失率 | < 5% |

## 相关方

| 角色 | 影响 |
|------|------|
| 最终用户 | 付费使用产品，需要流畅的注册付费体验 |
| 运营者 | 通过 Dashboard 查看用户状态，调整 tier_limits |

## 时间线

| 阶段 | 内容 | 周期 |
|------|------|------|
| Phase 1 | 方案设计 | 已完成 |
| Phase 2 | Website 升级 + Cloud API 开发 | 待定 |
| Phase 3 | 本地应用改造 | 待定 |
| Phase 4 | Stripe 集成测试 | 待定 |

## 关键决策记录

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 商业模式 | SaaS + 本地存储 + 云端 LLM | 用户信任度高，数据隐私友好 |
| 数据库 | PostgreSQL (Supabase/Neon) | Serverless，免费起步，托管简单 |
| 支付方案 | Stripe Checkout + Webhook | 行业标准，PCI 合规，订阅管理完善 |
| License 验证 | JWT Token + 云端验证 | 简单安全，支持离线降级 |
| LLM 调用方式 | Cloud API 代理 | 用户不需要配置 API Key，控制成本 |
| Tier limits | 数据库可配置，非硬编码 | 运营可随时调整，不需要重新部署 |
| 官网部署 | Vercel | 免费，全球 CDN，Next.js 原生支持 |
| 注册路径 | 双路径（官网 + 应用内） | 降低用户使用门槛 |
