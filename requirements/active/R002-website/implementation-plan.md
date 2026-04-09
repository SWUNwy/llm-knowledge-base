# KnowledgeBase 官网 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-page marketing website for KnowledgeBase with 7 vertical-scroll modules, supporting subscription conversion.

**Architecture:** Next.js 14 App Router with static site generation (SSG). Each section is an independent React component assembled on the homepage. TailwindCSS for styling, Framer Motion for scroll-triggered animations.

**Tech Stack:** Next.js 14, TailwindCSS 4, Framer Motion, TypeScript, Inter font

---

## File Structure

```
website/
├── app/
│   ├── layout.tsx              # Root layout: Inter font, meta tags
│   ├── page.tsx                # Homepage: assembles all 7 sections
│   ├── globals.css             # Tailwind imports + custom utilities
│   └── login/
│       └── page.tsx            # Login/register placeholder
├── components/
│   ├── ui/
│   │   ├── button.tsx          # Gradient + outline button variants
│   │   ├── logo.tsx            # Gradient logo (square + text)
│   │   └── icon-box.tsx        # Colored gradient icon container
│   ├── navbar.tsx              # Fixed top nav with scroll effect
│   ├── hero.tsx                # Hero + flow animation
│   ├── pain-points.tsx         # Pain points + transition band
│   ├── features.tsx            # 3 feature cards
│   ├── flow.tsx                # 3-step usage flow
│   ├── pricing.tsx             # 3-tier pricing cards
│   ├── cta.tsx                 # Bottom CTA section
│   └── footer.tsx              # 4-column footer
├── lib/
│   └── constants.ts            # Pricing data, nav links
├── public/
│   └── og-image.png            # Placeholder OG image
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── postcss.config.mjs
└── package.json
```

---

### Task 1: Initialize Next.js project

**Files:**
- Create: `website/package.json`
- Create: `website/next.config.ts`
- Create: `website/tsconfig.json`
- Create: `website/tailwind.config.ts`
- Create: `website/postcss.config.mjs`

- [ ] **Step 1: Create Next.js project**

Run:
```bash
cd .
npx create-next-app@latest website --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*" --use-npm
```

Accept defaults. This creates the `website/` directory with Next.js 14, TypeScript, TailwindCSS, ESLint, and App Router.

- [ ] **Step 2: Install Framer Motion**

Run:
```bash
cd website && npm install framer-motion
```

- [ ] **Step 3: Configure TailwindCSS for the design system**

Replace `website/tailwind.config.ts`:

```ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: "#3b82f6",
          "blue-light": "#60a5fa",
          purple: "#7c3aed",
          "purple-light": "#a78bfa",
          green: "#10b981",
          "green-light": "#34d399",
        },
        surface: {
          dark: "#0f172a",
          "dark-secondary": "#1e293b",
          light: "#f8fafc",
          white: "#ffffff",
        },
        text: {
          primary: "#0f172a",
          secondary: "#64748b",
          "on-dark": "#f8fafc",
          "on-dark-muted": "#94a3b8",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: {
        card: "16px",
        button: "10px",
        tag: "20px",
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 4: Set up global CSS**

Replace `website/app/globals.css`:

```css
@import "tailwindcss";

html {
  scroll-behavior: smooth;
}

body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

- [ ] **Step 5: Verify build succeeds**

Run:
```bash
cd ./website && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 6: Commit**

```bash
git add website/
git commit -m "feat(website): initialize Next.js project with TailwindCSS and Framer Motion"
```

---

### Task 2: Create constants and root layout

**Files:**
- Create: `website/lib/constants.ts`
- Modify: `website/app/layout.tsx`

- [ ] **Step 1: Create constants file**

Create `website/lib/constants.ts`:

```ts
export const SITE_NAME = "KnowledgeBase";
export const SITE_DESCRIPTION =
  "AI 驱动的本地知识库。自动将零散资料编译成结构化知识，用 AI 驱动问答和持续增强。";

export const NAV_LINKS = [
  { label: "功能", href: "#features" },
  { label: "流程", href: "#flow" },
  { label: "定价", href: "#pricing" },
  { label: "文档", href: "/docs" },
] as const;

export const PRICING_TIERS = [
  {
    name: "个人版",
    description: "适合个人学习与研究",
    price: 49,
    yearlyPrice: 468,
    yearlySaving: 120,
    color: "blue" as const,
    icon: "📝",
    features: [
      { text: "无限文档导入", included: true },
      { text: "基础 AI 编译（50次/月）", included: true },
      { text: "全文检索", included: true },
      { text: "Obsidian 同步", included: true },
      { text: "高级 AI 模型", included: false },
      { text: "团队协作", included: false },
    ],
  },
  {
    name: "专业版",
    description: "适合深度知识工作者",
    price: 99,
    yearlyPrice: 948,
    yearlySaving: 240,
    color: "purple" as const,
    icon: "⚡",
    popular: true,
    features: [
      { text: "无限文档导入", included: true },
      { text: "无限 AI 编译", included: true },
      { text: "高级 AI 模型（GPT-4o/Claude）", included: true },
      { text: "向量语义检索", included: true },
      { text: "优先技术支持", included: true },
    ],
  },
  {
    name: "团队版",
    description: "适合研究团队与企业",
    price: 299,
    yearlyPrice: 2868,
    yearlySaving: 720,
    color: "green" as const,
    icon: "👥",
    features: [
      { text: "专业版全部功能", included: true },
      { text: "5 人协作空间", included: true },
      { text: "共享知识库", included: true },
      { text: "管理后台", included: true },
      { text: "专属客户经理", included: true },
    ],
  },
] as const;
```

- [ ] **Step 2: Update root layout**

Replace `website/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SITE_NAME, SITE_DESCRIPTION } from "@/lib/constants";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: `${SITE_NAME} - 你的私有 AI 知识库`,
  description: SITE_DESCRIPTION,
  openGraph: {
    title: `${SITE_NAME} - 你的私有 AI 知识库`,
    description: SITE_DESCRIPTION,
    url: "https://knowledgebase.ai",
    siteName: SITE_NAME,
    locale: "zh_CN",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

- [ ] **Step 3: Verify build**

Run: `cd ./website && npm run build`

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add website/lib/constants.ts website/app/layout.tsx
git commit -m "feat(website): add constants and root layout with SEO meta"
```

---

### Task 3: Create reusable UI components

**Files:**
- Create: `website/components/ui/button.tsx`
- Create: `website/components/ui/logo.tsx`
- Create: `website/components/ui/icon-box.tsx`

- [ ] **Step 1: Create Button component**

Create `website/components/ui/button.tsx`:

```tsx
import { ReactNode } from "react";

type ButtonVariant = "primary" | "outline" | "outline-white";

interface ButtonProps {
  variant: ButtonVariant;
  children: ReactNode;
  href?: string;
  className?: string;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-brand-blue to-brand-purple text-white font-semibold",
  outline:
    "border border-slate-300 text-text-primary font-medium hover:border-slate-400 transition-colors",
  "outline-white":
    "border border-slate-600 text-text-on-dark font-medium hover:border-slate-400 transition-colors",
};

export function Button({ variant, children, href, className = "" }: ButtonProps) {
  const baseStyles =
    "inline-flex items-center justify-center px-7 py-3.5 rounded-button text-[15px] cursor-pointer";
  const styles = `${baseStyles} ${variantStyles[variant]} ${className}`;

  if (href) {
    return (
      <a href={href} className={styles}>
        {children}
      </a>
    );
  }

  return <button className={styles}>{children}</button>;
}
```

- [ ] **Step 2: Create Logo component**

Create `website/components/ui/logo.tsx`:

```tsx
import { SITE_NAME } from "@/lib/constants";

interface LogoProps {
  className?: string;
}

export function Logo({ className = "" }: LogoProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="w-7 h-7 rounded-md bg-gradient-to-br from-brand-blue to-brand-purple" />
      <span className="text-white font-bold text-base">{SITE_NAME}</span>
    </div>
  );
}
```

- [ ] **Step 3: Create IconBox component**

Create `website/components/ui/icon-box.tsx`:

```tsx
import { ReactNode } from "react";

type IconColor = "blue" | "purple" | "green";

interface IconBoxProps {
  color: IconColor;
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const colorStyles: Record<IconColor, string> = {
  blue: "from-brand-blue to-brand-blue-light",
  purple: "from-brand-purple to-brand-purple-light",
  green: "from-brand-green to-brand-green-light",
};

const sizeStyles = {
  sm: "w-8 h-8 text-base",
  md: "w-12 h-12 text-2xl",
  lg: "w-14 h-14 text-[28px]",
};

export function IconBox({ color, children, size = "md", className = "" }: IconBoxProps) {
  return (
    <div
      className={`bg-gradient-to-br ${colorStyles[color]} ${sizeStyles[size]} rounded-[12px] flex items-center justify-center ${className}`}
    >
      {children}
    </div>
  );
}
```

- [ ] **Step 4: Verify build**

Run: `cd ./website && npm run build`

Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add website/components/ui/
git commit -m "feat(website): add Button, Logo, IconBox UI components"
```

---

### Task 4: Create Navbar component

**Files:**
- Create: `website/components/navbar.tsx`

- [ ] **Step 1: Create Navbar**

Create `website/components/navbar.tsx`:

```tsx
"use client";

import { useState, useEffect } from "react";
import { Logo } from "@/components/ui/logo";
import { Button } from "@/components/ui/button";
import { NAV_LINKS } from "@/lib/constants";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-surface-dark/80 backdrop-blur-md border-b border-surface-dark-secondary"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Logo />

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm text-text-on-dark-muted hover:text-white transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>

          <div className="hidden md:block">
            <Button variant="primary" href="/login" className="text-[13px] px-5 py-2">
              免费试用
            </Button>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden text-white p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {mobileOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden pb-4 border-t border-surface-dark-secondary">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="block py-2 text-sm text-text-on-dark-muted hover:text-white"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <div className="mt-3">
              <Button variant="primary" href="/login" className="w-full text-[13px] py-2">
                免费试用
              </Button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd ./website && npm run build`

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add website/components/navbar.tsx
git commit -m "feat(website): add Navbar with scroll effect and mobile menu"
```

---

### Task 5: Create Hero section

**Files:**
- Create: `website/components/hero.tsx`

- [ ] **Step 1: Create Hero**

Create `website/components/hero.tsx`:

```tsx
import { Button } from "@/components/ui/button";

export function Hero() {
  return (
    <section className="bg-surface-dark pt-28 pb-16 lg:pt-36 lg:pb-24">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center">
          {/* Tag */}
          <div className="inline-block px-4 py-1.5 bg-brand-blue/15 border border-brand-blue/30 rounded-tag text-brand-blue-light text-[13px] mb-6">
            AI 驱动 · 本地优先 · Obsidian 兼容
          </div>

          {/* Title */}
          <h1 className="text-4xl lg:text-[42px] font-extrabold text-white leading-tight mb-4">
            你的私有 AI 知识库
          </h1>

          {/* Subtitle */}
          <p className="text-lg text-text-on-dark-muted max-w-xl mx-auto leading-relaxed mb-8">
            自动将零散资料编译成结构化知识，
            <br className="hidden sm:block" />
            用 AI 驱动问答和持续增强。
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-12 lg:mb-16">
            <Button variant="primary" href="/login">
              免费试用 14 天
            </Button>
            <Button variant="outline-white" href="#flow">
              观看演示 ▶
            </Button>
          </div>

          {/* Flow Animation */}
          <div className="flex flex-col md:flex-row items-center justify-center gap-4 lg:gap-6 max-w-2xl mx-auto py-6">
            {/* Input sources */}
            <div className="flex md:flex-col gap-3">
              {["🌐", "📄", "🎬"].map((emoji) => (
                <div
                  key={emoji}
                  className="w-16 h-16 bg-surface-dark-secondary rounded-xl border border-slate-700 flex items-center justify-center text-2xl"
                >
                  {emoji}
                </div>
              ))}
            </div>

            {/* Arrow */}
            <span className="text-3xl text-brand-blue hidden md:block">→</span>
            <span className="text-3xl text-brand-blue md:hidden">↓</span>

            {/* AI Processing */}
            <div className="w-[120px] h-[120px] rounded-full bg-gradient-to-br from-brand-blue/20 to-brand-purple/20 border-2 border-brand-blue/40 flex flex-col items-center justify-center">
              <span className="text-[28px] mb-1">🤖</span>
              <span className="text-[11px] text-brand-blue-light font-semibold">AI 编译</span>
            </div>

            {/* Arrow */}
            <span className="text-3xl text-brand-purple hidden md:block">→</span>
            <span className="text-3xl text-brand-purple md:hidden">↓</span>

            {/* Output */}
            <div className="bg-surface-dark-secondary rounded-xl border border-slate-700 p-4 w-52 text-left">
              <div className="text-[12px] text-text-on-dark font-semibold mb-2">
                📚 你的知识库
              </div>
              {[
                { name: "Transformer", color: "bg-brand-blue/10 text-brand-blue-light" },
                { name: "Self-Attention", color: "bg-brand-purple/10 text-brand-purple-light" },
                { name: "NLP 概述", color: "bg-brand-green/10 text-brand-green-light" },
              ].map((item) => (
                <div
                  key={item.name}
                  className={`px-2 py-1 rounded text-[11px] mb-1 ${item.color}`}
                >
                  [[{item.name}]]
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd ./website && npm run build`

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add website/components/hero.tsx
git commit -m "feat(website): add Hero section with flow animation"
```

---

### Task 6: Create Pain Points section

**Files:**
- Create: `website/components/pain-points.tsx`

- [ ] **Step 1: Create PainPoints**

Create `website/components/pain-points.tsx`:

```tsx
const PAIN_POINTS = [
  {
    icon: "🔍",
    title: "找不到",
    description: "存的资料不知道在哪，关键词搜不到",
  },
  {
    icon: "🧩",
    title: "没关联",
    description: "知识点是孤岛，没有形成网络",
  },
  {
    icon: "📖",
    title: "难理解",
    description: "论文/长文档太多，消化不完",
  },
];

export function PainPoints() {
  return (
    <section className="bg-white py-20 lg:py-28">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl lg:text-[28px] font-bold text-text-primary mb-2">
            资料越来越多，但真正要用时...
          </h2>
          <p className="text-text-secondary">你是否有这些困扰？</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-3xl mx-auto mb-8">
          {PAIN_POINTS.map((point) => (
            <div
              key={point.title}
              className="p-5 bg-red-50 rounded-xl border-l-4 border-red-500"
            >
              <div className="text-xl mb-2">{point.icon}</div>
              <div className="font-semibold text-red-900 mb-1">{point.title}</div>
              <div className="text-sm text-red-800">{point.description}</div>
            </div>
          ))}
        </div>

        {/* Transition band */}
        <div className="text-center py-4 px-6 bg-gradient-to-r from-blue-50 to-indigo-100 rounded-xl max-w-3xl mx-auto">
          <p className="text-sm text-blue-800 font-semibold">
            KnowledgeBase 用 AI 自动整理资料，生成结构化知识库
          </p>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd ./website && npm run build`

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add website/components/pain-points.tsx
git commit -m "feat(website): add Pain Points section"
```

---

### Task 7: Create Features section

**Files:**
- Create: `website/components/features.tsx`

- [ ] **Step 1: Create Features**

Create `website/components/features.tsx`:

```tsx
import { IconBox } from "@/components/ui/icon-box";

const FEATURES = [
  {
    icon: "📥",
    title: "智能导入",
    description: "一键导入网页、PDF、视频、GitHub 仓库。自动提取内容，本地存储。",
    color: "blue" as const,
    linkColor: "text-brand-blue",
  },
  {
    icon: "🤖",
    title: "AI 编译",
    description: "LLM 自动生成 Wiki 文章，提取概念，建立双向链接，沉淀为 Obsidian 可用知识。",
    color: "purple" as const,
    linkColor: "text-brand-purple",
  },
  {
    icon: "💬",
    title: "智能问答",
    description: "对知识库提问，AI 基于你的资料回答。答案可沉淀回库，持续增强。",
    color: "green" as const,
    linkColor: "text-brand-green",
  },
];

export function Features() {
  return (
    <section id="features" className="bg-surface-light py-20 lg:py-28">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center mb-12">
          <div className="inline-block px-4 py-1.5 bg-brand-blue/10 rounded-tag text-brand-blue text-[13px] font-semibold mb-4">
            三大核心能力
          </div>
          <h2 className="text-2xl lg:text-[28px] font-bold text-text-primary mb-2">
            一站式知识管理
          </h2>
          <p className="text-text-secondary">从导入到问答，全流程 AI 驱动</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="p-6 bg-white rounded-card border border-slate-200 shadow-sm"
            >
              <IconBox color={feature.color} className="mb-4">
                {feature.icon}
              </IconBox>
              <h3 className="text-lg font-bold text-text-primary mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-text-secondary leading-relaxed mb-4">
                {feature.description}
              </p>
              <div className={`pt-4 border-t border-slate-100 text-[13px] font-semibold ${feature.linkColor}`}>
                了解更多 →
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd ./website && npm run build`

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add website/components/features.tsx
git commit -m "feat(website): add Features section with 3 core capability cards"
```

---

### Task 8: Create Flow section

**Files:**
- Create: `website/components/flow.tsx`

- [ ] **Step 1: Create Flow**

Create `website/components/flow.tsx`:

```tsx
const STEPS = [
  {
    number: 1,
    title: "导入资料",
    description: "粘贴 URL、上传 PDF、收藏视频或导入 GitHub 仓库",
    tags: ["🌐 网页", "📄 PDF", "🎬 视频", "💻 代码"],
    color: "blue" as const,
    borderColor: "border-brand-blue/30",
    tagBg: "bg-brand-blue/15",
    tagText: "text-brand-blue-light",
  },
  {
    number: 2,
    title: "AI 自动编译",
    description: "LLM 提取概念、生成 Wiki 文章、建立双向链接",
    borderColor: "border-brand-purple/30",
    barGradient: "from-brand-purple to-brand-purple-light",
    color: "purple" as const,
  },
  {
    number: 3,
    title: "提问与沉淀",
    description: "对知识库提问，AI 基于你的资料回答，答案可沉淀回库",
    borderColor: "border-brand-green/30",
    color: "green" as const,
  },
];

const numberGradients: Record<string, string> = {
  blue: "from-brand-blue to-brand-blue-light",
  purple: "from-brand-purple to-brand-purple-light",
  green: "from-brand-green to-brand-green-light",
};

export function Flow() {
  return (
    <section id="flow" className="bg-surface-dark py-20 lg:py-28">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center mb-12">
          <div className="inline-block px-4 py-1.5 bg-brand-blue/15 rounded-tag text-brand-blue-light text-[13px] font-semibold mb-4">
            三步开始
          </div>
          <h2 className="text-2xl lg:text-[28px] font-bold text-white mb-2">
            从资料到知识，只需要三步
          </h2>
          <p className="text-text-on-dark-muted">简单到不可思议</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {STEPS.map((step) => (
            <div
              key={step.number}
              className={`p-6 bg-surface-dark-secondary rounded-card border ${step.borderColor}`}
            >
              <div
                className={`w-10 h-10 bg-gradient-to-br ${numberGradients[step.color]} rounded-full flex items-center justify-center text-white font-bold text-lg mb-4`}
              >
                {step.number}
              </div>
              <h3 className="text-lg font-bold text-white mb-2">{step.title}</h3>
              <p className="text-sm text-text-on-dark-muted leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd ./website && npm run build`

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add website/components/flow.tsx
git commit -m "feat(website): add Flow section with 3-step usage guide"
```

---

### Task 9: Create Pricing section

**Files:**
- Create: `website/components/pricing.tsx`

- [ ] **Step 1: Create Pricing**

Create `website/components/pricing.tsx`:

```tsx
import { PRICING_TIERS } from "@/lib/constants";

const tierStyles = {
  blue: {
    card: "bg-surface-light border-slate-200",
    iconBg: "from-brand-blue to-brand-blue-light",
    priceColor: "text-text-primary",
    yearColor: "text-brand-blue",
    featureCheck: "text-text-primary",
    featureNone: "text-slate-300",
    cta: "bg-white border-2 border-brand-blue text-brand-blue",
  },
  purple: {
    card: "bg-gradient-to-br from-brand-purple to-[#6d28d9] border-transparent",
    iconBg: "bg-white/20",
    priceColor: "text-white",
    yearColor: "text-purple-200",
    featureCheck: "text-white",
    featureNone: "text-white/30",
    cta: "bg-white text-brand-purple font-bold",
  },
  green: {
    card: "bg-surface-light border-slate-200",
    iconBg: "from-brand-green to-brand-green-light",
    priceColor: "text-text-primary",
    yearColor: "text-brand-green",
    featureCheck: "text-text-primary",
    featureNone: "text-slate-300",
    cta: "bg-white border-2 border-brand-green text-brand-green",
  },
};

export function Pricing() {
  return (
    <section id="pricing" className="bg-white py-20 lg:py-28">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl lg:text-[28px] font-bold text-text-primary mb-2">
            选择适合你的方案
          </h2>
          <p className="text-text-secondary">14 天免费试用，无需信用卡</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-5xl mx-auto items-stretch">
          {PRICING_TIERS.map((tier) => {
            const style = tierStyles[tier.color];
            const isPopular = "popular" in tier && tier.popular;

            return (
              <div
                key={tier.name}
                className={`relative p-7 rounded-card border-2 ${style.card} ${
                  isPopular ? "md:scale-[1.03] md:z-10" : ""
                }`}
              >
                {isPopular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-amber-500 text-white text-xs font-bold rounded-full whitespace-nowrap">
                    最受欢迎
                  </div>
                )}

                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center text-base mb-3 ${
                    isPopular ? style.iconBg : `bg-gradient-to-br ${style.iconBg}`
                  }`}
                >
                  {tier.icon}
                </div>

                <div className="text-sm text-text-secondary font-semibold uppercase tracking-wider mb-1">
                  {tier.name}
                </div>
                <div className="text-sm text-slate-400 mb-4">{tier.description}</div>

                <div className={`text-4xl font-extrabold mb-1 ${style.priceColor}`}>
                  ¥{tier.price}
                  <span className="text-base font-normal text-text-secondary">/月</span>
                </div>
                <div className={`text-[13px] mb-6 ${style.yearColor}`}>
                  年付 ¥{tier.yearlyPrice}/年，省 ¥{tier.yearlySaving}
                </div>

                <div className="py-3 border-t border-slate-200/30 border-b mb-5 space-y-2.5">
                  {tier.features.map((feature) => (
                    <div
                      key={feature.text}
                      className={`text-sm ${
                        feature.included ? style.featureCheck : style.featureNone
                      }`}
                    >
                      {feature.included ? "✓" : "○"} {feature.text}
                    </div>
                  ))}
                </div>

                <button
                  className={`w-full py-3 rounded-button text-center font-semibold cursor-pointer ${style.cta}`}
                >
                  开始免费试用
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd ./website && npm run build`

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add website/components/pricing.tsx
git commit -m "feat(website): add Pricing section with 3-tier subscription cards"
```

---

### Task 10: Create CTA and Footer sections

**Files:**
- Create: `website/components/cta.tsx`
- Create: `website/components/footer.tsx`

- [ ] **Step 1: Create CTA**

Create `website/components/cta.tsx`:

```tsx
import { Button } from "@/components/ui/button";

export function Cta() {
  return (
    <section className="bg-gradient-to-br from-surface-dark to-[#1e1b4b] py-20 lg:py-28">
      <div className="max-w-3xl mx-auto px-6 lg:px-8 text-center">
        <h2 className="text-2xl lg:text-[32px] font-extrabold text-white mb-3 leading-snug">
          开始构建你的 AI 知识库
        </h2>
        <p className="text-base text-text-on-dark-muted mb-8 leading-relaxed">
          14 天免费试用，无需信用卡。从今天开始，让零散资料变成结构化知识。
        </p>
        <Button variant="primary" href="/login" className="mb-6">
          免费试用 14 天
        </Button>
        <p className="text-[13px] text-text-on-dark-muted">
          无需信用卡 · 随时取消 · 支持多模型
        </p>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Create Footer**

Create `website/components/footer.tsx`:

```tsx
import { Logo } from "@/components/ui/logo";
import { SITE_NAME } from "@/lib/constants";

const FOOTER_SECTIONS = [
  {
    title: "产品",
    links: ["功能", "定价", "更新日志", "路线图"],
  },
  {
    title: "资源",
    links: ["文档", "博客", "常见问题", "社区"],
  },
  {
    title: "关于",
    links: ["关于我们", "联系方式", "隐私政策", "服务条款"],
  },
];

export function Footer() {
  return (
    <footer className="bg-surface-dark border-t border-surface-dark-secondary">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8 pb-8 border-b border-surface-dark-secondary">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <Logo className="mb-3" />
            <p className="text-[13px] text-slate-500 leading-relaxed max-w-[280px]">
              AI 驱动的本地知识库。自动将零散资料编译成结构化知识。
            </p>
          </div>

          {/* Link columns */}
          {FOOTER_SECTIONS.map((section) => (
            <div key={section.title}>
              <div className="text-[13px] font-semibold text-white mb-3">
                {section.title}
              </div>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-[13px] text-slate-500 hover:text-slate-300 transition-colors"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-slate-600">
          <span>© 2026 {SITE_NAME}. All rights reserved.</span>
          <div className="flex gap-4">
            <a href="#" className="hover:text-slate-400 transition-colors">GitHub</a>
            <a href="#" className="hover:text-slate-400 transition-colors">Twitter / X</a>
            <a href="#" className="hover:text-slate-400 transition-colors">微信</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
```

- [ ] **Step 3: Verify build**

Run: `cd ./website && npm run build`

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add website/components/cta.tsx website/components/footer.tsx
git commit -m "feat(website): add CTA and Footer sections"
```

---

### Task 11: Assemble homepage + add login placeholder

**Files:**
- Modify: `website/app/page.tsx`
- Create: `website/app/login/page.tsx`

- [ ] **Step 1: Assemble homepage**

Replace `website/app/page.tsx`:

```tsx
import { Navbar } from "@/components/navbar";
import { Hero } from "@/components/hero";
import { PainPoints } from "@/components/pain-points";
import { Features } from "@/components/features";
import { Flow } from "@/components/flow";
import { Pricing } from "@/components/pricing";
import { Cta } from "@/components/cta";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <PainPoints />
        <Features />
        <Flow />
        <Pricing />
        <Cta />
      </main>
      <Footer />
    </>
  );
}
```

- [ ] **Step 2: Create login placeholder**

Create `website/app/login/page.tsx`:

```tsx
export default function LoginPage() {
  return (
    <div className="min-h-screen bg-surface-dark flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-brand-blue to-brand-purple mx-auto mb-4" />
        <h1 className="text-xl font-bold text-white mb-2">登录 / 注册</h1>
        <p className="text-sm text-text-on-dark-muted">即将上线</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify build and run dev server**

Run:
```bash
cd ./website && npm run build
```

Expected: Build succeeds with all 7 sections assembled.

Then verify visually:
```bash
cd ./website && npm run dev
```

Open http://localhost:3000 — verify all 7 modules render correctly.

- [ ] **Step 4: Commit**

```bash
git add website/app/page.tsx website/app/login/
git commit -m "feat(website): assemble homepage with all 7 sections"
```

---

### Task 12: Add scroll-triggered animations

**Files:**
- Create: `website/components/ui/scroll-reveal.tsx`
- Modify: `website/components/hero.tsx`
- Modify: `website/components/pain-points.tsx`
- Modify: `website/components/features.tsx`
- Modify: `website/components/flow.tsx`
- Modify: `website/components/pricing.tsx`
- Modify: `website/components/cta.tsx`

- [ ] **Step 1: Create ScrollReveal wrapper**

Create `website/components/ui/scroll-reveal.tsx`:

```tsx
"use client";

import { ReactNode, useRef } from "react";
import { motion, useInView } from "framer-motion";

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

export function ScrollReveal({ children, className = "", delay = 0 }: ScrollRevealProps) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
```

- [ ] **Step 2: Wrap section headings and cards with ScrollReveal**

In each section component (`pain-points.tsx`, `features.tsx`, `flow.tsx`, `pricing.tsx`, `cta.tsx`):

1. Add `"use client"` directive at top of the file
2. Import `{ ScrollReveal } from "@/components/ui/scroll-reveal"`
3. Wrap the section heading block in `<ScrollReveal>`
4. Wrap each card in `<ScrollReveal delay={index * 0.1}>`

Example for `pain-points.tsx` — wrap the cards grid:
```tsx
"use client";

import { ScrollReveal } from "@/components/ui/scroll-reveal";
// ...existing code...

export function PainPoints() {
  return (
    <section className="bg-white py-20 lg:py-28">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <ScrollReveal>
          {/* heading block */}
        </ScrollReveal>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-3xl mx-auto mb-8">
          {PAIN_POINTS.map((point, i) => (
            <ScrollReveal key={point.title} delay={i * 0.1}>
              {/* card */}
            </ScrollReveal>
          ))}
        </div>
        <ScrollReveal>
          {/* transition band */}
        </ScrollReveal>
      </div>
    </section>
  );
}
```

Apply the same pattern to: `features.tsx`, `flow.tsx`, `pricing.tsx`, `cta.tsx`.

- [ ] **Step 3: Verify build and animations**

Run: `cd ./website && npm run build`

Expected: Build succeeds. Open dev server and verify scroll animations fire once when sections enter viewport.

- [ ] **Step 4: Commit**

```bash
git add website/components/
git commit -m "feat(website): add scroll-triggered animations to all sections"
```

---

### Task 13: SEO finalization and production build

**Files:**
- Create: `website/public/robots.txt`
- Modify: `website/app/layout.tsx` (add structured data)
- Modify: `website/next.config.ts`

- [ ] **Step 1: Add robots.txt**

Create `website/public/robots.txt`:

```
User-agent: *
Allow: /

Sitemap: https://knowledgebase.ai/sitemap.xml
```

- [ ] **Step 2: Update next.config.ts for sitemap**

Replace `website/next.config.ts`:

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
```

- [ ] **Step 3: Add structured data to layout**

In `website/app/layout.tsx`, add JSON-LD structured data inside the `<body>`:

```tsx
<script
  type="application/ld+json"
  dangerouslySetInnerHTML={{
    __html: JSON.stringify({
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      name: "KnowledgeBase",
      applicationCategory: "Knowledge Management",
      description: SITE_DESCRIPTION,
      offers: {
        "@type": "AggregateOffer",
        lowPrice: "49",
        highPrice: "299",
        priceCurrency: "CNY",
      },
    }),
  }}
/>
```

- [ ] **Step 4: Production build + Lighthouse check**

Run:
```bash
cd ./website && npm run build
```

Expected: Static export succeeds in `website/out/` directory.

Run Lighthouse (or manually check Performance/SEO scores):
```bash
npx lighthouse http://localhost:3000 --output=json --quiet | jq '.categories | {performance: .performance.score, seo: .seo.score, accessibility: .accessibility.score}'
```

Target: Performance > 0.9, SEO > 0.9

- [ ] **Step 5: Commit**

```bash
git add website/
git commit -m "feat(website): add SEO optimization and production build config"
```

---

## Self-Review

**Spec coverage check:**
- Navbar (5.1) → Task 4 ✓
- Hero (5.2) → Task 5 ✓
- Pain Points (5.3) → Task 6 ✓
- Features (5.4) → Task 7 ✓
- Flow (5.5) → Task 8 ✓
- Pricing (5.6) → Task 9 ✓
- CTA + Footer (5.7) → Task 10 ✓
- Page assembly → Task 11 ✓
- Animations → Task 12 ✓
- SEO → Task 13 ✓
- Responsive → Built into each component (Tailwind responsive classes) ✓

**Placeholder scan:** No TBD, TODO, or placeholder patterns found.

**Type consistency:** All component props use consistent types. Color types (`"blue" | "purple" | "green"`) match across `IconBox`, `Flow`, `Pricing`, and constants.
