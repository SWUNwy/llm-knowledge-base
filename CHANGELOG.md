# Changelog

## 2026-04-09: 官网上线（Phase 1 MVP）

### 新增

- **官网首页** (`website/`)：单页长滚动营销官网，7 个模块垂直滚动
  - Navbar：固定顶部导航，滚动模糊背景，移动端汉堡菜单
  - Hero：深色背景，流程动画（资料来源 → AI 编译 → 知识库输出），双 CTA
  - 痛点共鸣：3 个红色卡片（找不到/没关联/难理解）+ 蓝色过渡带
  - 核心功能：3 个功能卡片（智能导入/AI 编译/智能问答）
  - 使用流程：3 步卡片（导入 → 编译 → 沉淀）
  - 定价：三档方案（个人版 ¥49 / 专业版 ¥99 / 团队版 ¥299）
  - 底部 CTA + Footer（四列布局 + 社交链接）
- **登录页占位** (`website/app/login/`)
- **ScrollReveal 动画**：基于 Framer Motion 的滚动触发动画
- **SEO 基础**：meta/OG、JSON-LD 结构化数据、robots.txt、静态导出

### 技术栈

- Next.js 16 + TypeScript + TailwindCSS v3 + Framer Motion

### 规范文档

- `requirements/active/R002-website/` — 完整 SDD 文档（proposal/design/tasks/test-cases/implementation-plan）
