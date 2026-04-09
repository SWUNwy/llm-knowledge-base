"use client";

import { ScrollReveal } from "@/components/ui/scroll-reveal";

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
        <ScrollReveal>
          <div className="text-center mb-12">
            <h2 className="text-2xl lg:text-[28px] font-bold text-text-primary mb-2">
              资料越来越多，但真正要用时...
            </h2>
            <p className="text-text-secondary">你是否有这些困扰？</p>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-3xl mx-auto mb-8">
          {PAIN_POINTS.map((point, i) => (
            <ScrollReveal key={point.title} delay={i * 0.1}>
              <div className="p-5 bg-red-50 rounded-xl border-l-4 border-red-500">
                <div className="text-xl mb-2">{point.icon}</div>
                <div className="font-semibold text-red-900 mb-1">{point.title}</div>
                <div className="text-sm text-red-800">{point.description}</div>
              </div>
            </ScrollReveal>
          ))}
        </div>

        <ScrollReveal>
          <div className="text-center py-4 px-6 bg-gradient-to-r from-blue-50 to-indigo-100 rounded-xl max-w-3xl mx-auto">
            <p className="text-sm text-blue-800 font-semibold">
              KnowledgeBase 用 AI 自动整理资料，生成结构化知识库
            </p>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
