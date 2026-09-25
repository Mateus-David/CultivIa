import type { ComponentProps } from "react";

export function Button(props: ComponentProps<"button">) {
  return (
    <button
      className="cursor-pointer rounded-lg bg-verde px-3.5 py-2 font-semibold text-verde-escuro transition hover:brightness-110"
      {...props}
    />
  );
}
