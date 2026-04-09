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
          <div className="col-span-2 md:col-span-1">
            <Logo className="mb-3" />
            <p className="text-[13px] text-slate-500 leading-relaxed max-w-[280px]">
              AI 驱动的本地知识库。自动将零散资料编译成结构化知识。
            </p>
          </div>

          {FOOTER_SECTIONS.map((section) => (
            <div key={section.title}>
              <div className="text-[13px] font-semibold text-white mb-3">{section.title}</div>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-[13px] text-slate-500 hover:text-slate-300 transition-colors">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-slate-600">
          <span>&copy; 2026 {SITE_NAME}. All rights reserved.</span>
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
