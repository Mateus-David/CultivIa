// StatusPill — etiqueta arredondada verde (ok) ou vermelha (problema).
import type { ReactNode } from "react";

type StatusPillProps = {
  ok: boolean;
  children: ReactNode;
};

export function StatusPill({ ok, children }: StatusPillProps) {
  const cores = ok ? "bg-verde/15 text-verde" : "bg-vermelho/15 text-vermelho";
  return <span className={`rounded-full px-2.5 py-1 text-sm font-semibold ${cores}`}>{children}</span>;
}
