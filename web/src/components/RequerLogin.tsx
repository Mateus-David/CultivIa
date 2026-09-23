// RequerLogin — "porteiro": só mostra o conteúdo se houver token guardado.
// Sem token, manda para /login.
//
//   <RequerLogin>
//     <Painel />          <- só aparece depois da checagem
//   </RequerLogin>
//
// Por que useEffect? O Next.js desenha a página primeiro no SERVIDOR, onde
// não existe sessionStorage. O efeito só roda no navegador, depois do
// primeiro desenho — até lá mostramos nada (null).
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { token } from "@/lib/token";

export function RequerLogin({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [liberado, setLiberado] = useState(false);

  useEffect(() => {
    if (token.ler()) setLiberado(true);
    else router.replace("/login");
  }, [router]);

  return liberado ? children : null;
}
