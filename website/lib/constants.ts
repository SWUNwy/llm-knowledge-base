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
