import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "CultivIa",
  description: "Monitoramento e controle da estufa",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-fundo px-4 pb-8 text-texto antialiased">{children}</body>
    </html>
  );
}
