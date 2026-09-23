// Card — a "caixa" usada em todo bloco da tela.
//
// `children` é o que você coloca ENTRE as tags:
//   <Card titulo="Atuadores"> ...isto é o children... </Card>
import type { ReactNode } from "react";

type CardProps = {
  titulo?: string;       // `?` = opcional
  className?: string;    // classes extras de quem usa
  children: ReactNode;
};

export function Card({ titulo, className = "", children }: CardProps) {
  return (
    <section className={`flex flex-col gap-3 rounded-xl border border-borda bg-cartao p-4 ${className}`}>
      {titulo && <h2 className="font-semibold text-apagado">{titulo}</h2>}
      {children}
    </section>
  );
}
