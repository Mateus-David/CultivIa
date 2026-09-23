// web/src/hooks/useComando.ts — envia comandos para a placa e trata o erro.
//
// Uso:
//   const { executar, erro } = useComando(atualizar);
//   executar(() => api.alternarAtuador("luz", true));
//
// Depois de um comando dar certo, chama `aoConcluir` meio segundo depois
// para a tela buscar o estado novo. A tela mostra o que a PLACA confirma
// (via cultivia/estado), não o que foi clicado — por isso pode levar ~2 s.
import { useCallback, useState } from "react";
import { mensagemDeErro } from "@/lib/api";

export function useComando(aoConcluir: () => void) {
  const [erro, setErro] = useState("");

  const executar = useCallback(
    async (acao: () => Promise<unknown>) => {
      try {
        await acao();
        setErro("");
        setTimeout(aoConcluir, 500);
      } catch (e) {
        setErro(mensagemDeErro(e));
      }
    },
    [aoConcluir],
  );

  return { executar, erro };
}
