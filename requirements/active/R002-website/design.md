# R002 - 官网技术设计

## 概述

基于 SDD Phase 1 的需求，采用渐进式策略：Phase 1 实现单页长滚动官网，Phase 2 拆分扩展为多页站点。

详细设计文档见：`requirements/active/R002-website/website-design.md`

## 技术栈

| 层级 | 技术 | 选型理由 |
|------|------|----------|
| 框架 | Next.js 14 (App Router) | SSG 静态生成，SEO 友好，React 生态 |
| 样式 | TailwindCSS 4 | 快速开发，原子化 CSS，与产品前端一致 |
| 动画 | Framer Motion | 滚动触发动画、Hero 流程动画 |
| 部署 | Vercel | 与 Next.js 深度集成，自动部署 |
| 分析 | Plausible | 隐私友好，无 Cookie |

## 站点结构

### Phase 1

```
website/
├── app/
│   ├── layout.tsx          # 根布局（字体、meta）
│   ├── page.tsx            # 首页（单页 7 模块）
│   └── login/
│       └── page.tsx        # 登录/注册
├── components/
│   ├── navbar.tsx          # 固定导航
│   ├── hero.tsx            # Hero 区
│   ├── pain-points.tsx     # 痛点共鸣区
│   ├── features.tsx        # 核心功能区
│   ├── flow.tsx            # 使用流程区
│   ├── pricing.tsx         # 定价区
│   ├── cta.tsx             # 底部 CTA
│   └── footer.tsx          # Footer
├── public/                 # 静态资源
│   ├── images/
│   └── og-image.png
└── package.json
```

### Phase 2（扩展）

```
├── app/
│   ├── pricing/page.tsx
│   ├── docs/
│   │   ├── page.tsx              # 文档首页
│   │   ├── getting-started/
│   │   ├── import/
│   │   ├── compilation/
│   │   ├── qa/
│   │   ├── obsidian/
│   │   ├── llm-config/
│   │   └── faq/
│   └── blog/
```

## 首页模块设计

### 整体节奏

```
深(Hero) → 浅(痛点) → 浅灰(功能) → 深(流程) → 白(定价) → 深(CTA+Footer)
```

### 模块 1: Navbar

- 固定顶部，滚动后添加半透明模糊背景
- 左侧 Logo + 中间锚点导航 + 右侧 CTA 按钮

### 模块 2: Hero（深色 `#0f172a`）

- 标签：AI 驱动 · 本地优先 · Obsidian 兼容
- 主标题：你的私有 AI 知识库
- 流程动画：资料来源 → AI 编译 → 知识库输出
- 双按钮：免费试用 14 天 + 观看演示

### 模块 3: 痛点共鸣（白色）

- 3 个红色卡片：找不到 / 没关联 / 难理解
- 蓝色过渡带引出解决方案

### 模块 4: 核心功能（浅灰 `#f8fafc`）

- 3 个功能卡片：智能导入(蓝) / AI 编译(紫) / 智能问答(绿)

### 模块 5: 使用流程（深色 `#0f172a`）

- 3 步卡片：导入(蓝) → AI 编译(紫) → 提问沉淀(绿)

### 模块 6: 定价（白色）

- 三档：个人版 ¥49(蓝) / 专业版 ¥99(紫，推荐) / 团队版 ¥299(绿)

### 模块 7: 底部 CTA + Footer

- 深蓝→深紫渐变背景 CTA
- 四列 Footer：品牌 / 产品 / 资源 / 关于

## 视觉系统

### 色彩

| 用途 | 色值 |
|------|------|
| 主色蓝 | `#3b82f6` → `#60a5fa` |
| 辅色紫 | `#7c3aed` → `#a78bfa` |
| 点缀绿 | `#10b981` → `#34d399` |
| 主文字 | `#0f172a` |
| 次要文字 | `#64748b` |
| 深色背景 | `#0f172a` |
| CTA 渐变 | `#0f172a` → `#1e1b4b` |

### 字体

- 中文：系统默认
- 英文：Inter
- 代码：monospace

## 响应式断点

| 断点 | 宽度 | 布局调整 |
|------|------|----------|
| 桌面 | ≥1024px | 默认布局 |
| 平板 | 768-1023px | 卡片 2 列，间距缩小 |
| 手机 | <768px | 单列，汉堡菜单，简化动画 |

## 性能要求

| 指标 | 目标 |
|------|------|
| LCP | < 2.5s |
| FID | < 100ms |
| CLS | < 0.1 |
| Lighthouse | > 90 |

## SEO

- 每页独立 meta title/description
- Open Graph 图片
- 结构化数据（Product, FAQ）
- sitemap.xml / robots.txt
