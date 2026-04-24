import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tipster Monitor",
  description: "Plataforma de monitoramento e análise de tipsters do YouTube",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
