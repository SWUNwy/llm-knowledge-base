"use client";

import { Button } from "@/components/ui/button";
import { ScrollReveal } from "@/components/ui/scroll-reveal";

export function Cta() {
  return (
    <section className="bg-gradient-to-br from-surface-dark to-[#1e1b4b] py-20 lg:py-28">
      <div className="max-w-3xl mx-auto px-6 lg:px-8 text-center">
        <ScrollReveal>
          <h2 className="text-2xl lg:text-[32px] font-extrabold text-white mb-3 leading-snug">
            开始构建你的 AI 知识库
          </h2>
        </ScrollReveal>
        <ScrollReveal delay={0.1}>
          <p className="text-base text-text-on-dark-muted mb-8 leading-relaxed">
            14 天免费试用，无需信用卡。从今天开始，让零散资料变成结构化知识。
          </p>
        </ScrollReveal>
        <ScrollReveal delay={0.2}>
          <Button variant="primary" href="/login" className="mb-6">
            免费试用 14 天
          </Button>
        </ScrollReveal>
        <ScrollReveal delay={0.3}>
          <p className="text-[13px] text-text-on-dark-muted">
            无需信用卡 · 随时取消 · 支持多模型
          </p>
        </ScrollReveal>
      </div>
    </section>
  );
}
