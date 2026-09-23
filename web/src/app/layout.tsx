// web/src/app/layout.tsx — a "moldura" de TODAS as páginas (<html> e <body>).
//
// App Router: cada pasta dentro de src/app/ é uma rota.
//   src/app/(painel)/page.tsx  ->  /        ("(...)" não entra na URL)
//   src/app/login/page.tsx     ->  /login
// O layout envolve as duas; `children` é a página da rota atual.
//
// ONDE FICA CADA COMPONENTE:
//   app/<rota>/_components/   usado SÓ por aquela tela. O "_" diz ao Next.js
//                             que a pasta é privada (não vira rota).
//   src/components/           usado por MAIS de uma tela (Card, Button...).
// Quando um componente de _components/ passar a ser usado por outra tela,
// mova-o para src/components/.
import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

// Vira o <title> e a <meta description> da página
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
