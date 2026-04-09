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
      <body>{children}</body>
    </html>
  );
}
