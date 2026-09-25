import { useCallback, useEffect, useState } from "react";
import { api, mensagemDeErro } from "@/lib/api";
import type { Estado } from "@/lib/types";

// pergunta o estado da placa pra API de tempos em tempos
export function useEstado(intervaloMs = 2000) {
  const [estado, setEstado] = useState<Estado | null>(null);
  const [erro, setErro] = useState("");

  const atualizar = useCallback(async () => {
    try {
      setEstado(await api.estado());
      setErro("");
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  }, []);

  useEffect(() => {
    atualizar();
    const id = setInterval(atualizar, intervaloMs);
    return () => clearInterval(id);
  }, [atualizar, intervaloMs]);

  return { estado, erro, atualizar };
}
