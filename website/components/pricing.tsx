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
