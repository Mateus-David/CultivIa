// Button — botão com variações de estilo.
//
//   <Button onClick={...}>Aplicar</Button>                 verde cheio (padrão)
//   <Button variante="secundario">Pausar</Button>          só contorno
//   <Button variante="link">Sair</Button>                  parece um link
import type { ComponentProps } from "react";

const VARIANTES = {
  primario: "px-3.5 py-2 bg-verde text-verde-escuro hover:brightness-110",
  secundario: "px-3.5 py-2 border border-borda text-texto hover:bg-borda/50",
  link: "text-apagado font-normal hover:text-texto",
};

// ComponentProps<"button"> = todas as props de um <button> comum
// (onClick, disabled, type...). Somamos a nossa `variante`.
type ButtonProps = ComponentProps<"button"> & {
  variante?: keyof typeof VARIANTES;   // "primario" | "secundario" | "link"
};

export function Button({ variante = "primario", className = "", ...resto }: ButtonProps) {
  return (
    <button
      className={`cursor-pointer rounded-lg font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${VARIANTES[variante]} ${className}`}
      {...resto}   // repassa onClick, disabled, children... para o <button>
    />
  );
}
