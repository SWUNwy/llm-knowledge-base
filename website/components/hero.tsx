import { Button } from "@/components/ui/button";

export function Hero() {
  return (
    <section className="bg-surface-dark pt-28 pb-16 lg:pt-36 lg:pb-24">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center">
          <div className="inline-block px-4 py-1.5 bg-brand-blue/15 border border-brand-blue/30 rounded-tag text-brand-blue-light text-[13px] mb-6">
            AI 驱动 · 本地优先 · Obsidian 兼容
          </div>

          <h1 className="text-4xl lg:text-[42px] font-extrabold text-white leading-tight mb-4">
            你的私有 AI 知识库
          </h1>

          <p className="text-lg text-text-on-dark-muted max-w-xl mx-auto leading-relaxed mb-8">
            自动将零散资料编译成结构化知识，
            <br className="hidden sm:block" />
            用 AI 驱动问答和持续增强。
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-12 lg:mb-16">
            <Button variant="primary" href="/login">
              免费试用 14 天
            </Button>
            <Button variant="outline-white" href="#flow">
              观看演示 ▶
            </Button>
          </div>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4 lg:gap-6 max-w-2xl mx-auto py-6">
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

            <span className="text-3xl text-brand-blue hidden md:block">→</span>
            <span className="text-3xl text-brand-blue md:hidden">↓</span>

            <div className="w-[120px] h-[120px] rounded-full bg-gradient-to-br from-brand-blue/20 to-brand-purple/20 border-2 border-brand-blue/40 flex flex-col items-center justify-center">
              <span className="text-[28px] mb-1">🤖</span>
              <span className="text-[11px] text-brand-blue-light font-semibold">AI 编译</span>
            </div>

            <span className="text-3xl text-brand-purple hidden md:block">→</span>
            <span className="text-3xl text-brand-purple md:hidden">↓</span>

            <div className="bg-surface-dark-secondary rounded-xl border border-slate-700 p-4 w-52 text-left">
              <div className="text-[12px] text-text-on-dark font-semibold mb-2">📚 你的知识库</div>
              {[
                { name: "Transformer", color: "bg-brand-blue/10 text-brand-blue-light" },
                { name: "Self-Attention", color: "bg-brand-purple/10 text-brand-purple-light" },
                { name: "NLP 概述", color: "bg-brand-green/10 text-brand-green-light" },
              ].map((item) => (
                <div key={item.name} className={`px-2 py-1 rounded text-[11px] mb-1 ${item.color}`}>
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
