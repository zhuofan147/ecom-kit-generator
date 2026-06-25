import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "电商套图生成工具",
  description: "本地开发版电商白底主图生成工具"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
