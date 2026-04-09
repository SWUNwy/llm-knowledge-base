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
              <h3 className="text-lg font-bold text-text-primary mb-2">{feature.title}</h3>
              <p className="text-sm text-text-secondary leading-relaxed mb-4">{feature.description}</p>
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
