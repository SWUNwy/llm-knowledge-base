export const SITE_NAME = "KnowledgeBase";
export const SITE_DESCRIPTION = "KnowledgeBase 是一个基于 AI 的智能知识管理系统，帮助你轻松组织和检索各类文档、视频、网页等内容。";

export const NAV_LINKS = [
  { label: "功能", href: "#features" },
  { label: "使用场景", href: "#use-cases" },
  { label: "价格", href: "#pricing" },
  { label: "关于", href: "#about" },
] as const;

export const PRICING_TIERS = [
  {
    name: "Starter",
    description: "适合个人用户",
    price: 0,
    yearlyPrice: 0,
    yearlySaving: 0,
    icon: "🚀",
    color: "blue" as const,
    features: [
      { text: "最多 50 篇文档", included: true },
      { text: "5 次/天 AI 编译", included: true },
      { text: "基础智能问答", included: true },
      { text: "GitHub 仓库导入", included: false },
      { text: "API 访问", included: false },
    ],
  },
  {
    name: "Pro",
    description: "适合专业用户和小团队",
    price: 49,
    yearlyPrice: 468,
    yearlySaving: 120,
    icon: "⚡",
    color: "purple" as const,
    popular: true,
    features: [
      { text: "无限文档", included: true },
      { text: "无限 AI 编译", included: true },
      { text: "高级智能问答", included: true },
      { text: "GitHub 仓库导入", included: true },
      { text: "API 访问", included: true },
    ],
  },
  {
    name: "Team",
    description: "适合企业和大型团队",
    price: 149,
    yearlyPrice: 1428,
    yearlySaving: 360,
    icon: "🏢",
    color: "green" as const,
    features: [
      { text: "无限文档", included: true },
      { text: "无限 AI 编译", included: true },
      { text: "高级智能问答", included: true },
      { text: "GitHub 仓库导入", included: true },
      { text: "API 访问 + 优先支持", included: true },
    ],
  },
];
