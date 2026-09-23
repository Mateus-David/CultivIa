// web/src/hooks/useEstado.ts — busca o estado da placa de tempos em tempos.
//
// Hook = função que começa com "use" e pode usar outros hooks (useState,
// useEffect...). Serve para tirar LÓGICA de dentro dos componentes: o Painel
// só chama useEstado() e recebe os dados prontos.
//
// POLLING: o navegador PERGUNTA a cada X ms (a API não "empurra" nada).
import { useCallback, useEffect, useState } from "react";
import { api, mensagemDeErro } from "@/lib/api";
import type { Estado } from "@/lib/types";

export function useEstado(intervaloMs = 2000) {
  const [estado, setEstado] = useState<Estado | null>(null);   // null = ainda não chegou
  const [erro, setErro] = useState("");

  // useCallback mantém a MESMA função entre redesenhos; sem ele, o
  // useEffect abaixo recriaria o timer a cada redesenho.
  const atualizar = useCallback(async () => {
    try {
      setEstado(await api.estado());
      setErro("");
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  }, []);

  // Roda quando o componente aparece. O `return` é a LIMPEZA: quando ele
  // some (ex.: logout), o timer é cancelado.
  useEffect(() => {
    atualizar();
    const id = setInterval(atualizar, intervaloMs);
    return () => clearInterval(id);
  }, [atualizar, intervaloMs]);

  return { estado, erro, atualizar };
}
