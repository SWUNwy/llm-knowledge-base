"use client";

import { ScrollReveal } from "@/components/ui/scroll-reveal";

const STEPS = [
  {
    number: 1,
    title: "导入资料",
    description: "粘贴 URL、上传 PDF、收藏视频或导入 GitHub 仓库",
    color: "blue" as const,
    borderColor: "border-brand-blue/30",
  },
  {
    number: 2,
    title: "AI 自动编译",
    description: "LLM 提取概念、生成 Wiki 文章、建立双向链接",
    color: "purple" as const,
    borderColor: "border-brand-purple/30",
  },
  {
    number: 3,
    title: "提问与沉淀",
    description: "对知识库提问，AI 基于你的资料回答，答案可沉淀回库",
    color: "green" as const,
    borderColor: "border-brand-green/30",
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
        <ScrollReveal>
          <div className="text-center mb-12">
            <div className="inline-block px-4 py-1.5 bg-brand-blue/15 rounded-tag text-brand-blue-light text-[13px] font-semibold mb-4">
              三步开始
            </div>
            <h2 className="text-2xl lg:text-[28px] font-bold text-white mb-2">
              从资料到知识，只需要三步
            </h2>
            <p className="text-text-on-dark-muted">简单到不可思议</p>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {STEPS.map((step, i) => (
            <ScrollReveal key={step.number} delay={i * 0.1}>
              <div
                className={`p-6 bg-surface-dark-secondary rounded-card border ${step.borderColor}`}
              >
                <div
                  className={`w-10 h-10 bg-gradient-to-br ${numberGradients[step.color]} rounded-full flex items-center justify-center text-white font-bold text-lg mb-4`}
                >
                  {step.number}
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{step.title}</h3>
                <p className="text-sm text-text-on-dark-muted leading-relaxed">{step.description}</p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
