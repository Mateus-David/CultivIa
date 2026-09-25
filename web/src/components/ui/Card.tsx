import type { ReactNode } from "react";

type CardProps = {
  titulo?: string;
  children: ReactNode;
};

export function Card({ titulo, children }: CardProps) {
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-borda bg-cartao p-4">
      {titulo && <h2 className="font-semibold text-apagado">{titulo}</h2>}
      {children}
    </section>
  );
}
