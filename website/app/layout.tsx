import type { Metadata } from "next";
import "./globals.css";
import { SITE_NAME, SITE_DESCRIPTION } from "@/lib/constants";

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
      <body>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              name: "KnowledgeBase",
              applicationCategory: "Knowledge Management",
              description: "AI 驱动的本地知识库。自动将零散资料编译成结构化知识，用 AI 驱动问答和持续增强。",
              offers: {
                "@type": "AggregateOffer",
                lowPrice: "49",
                highPrice: "299",
                priceCurrency: "CNY",
              },
            }),
          }}
        />
        {children}
      </body>
    </html>
  );
}
