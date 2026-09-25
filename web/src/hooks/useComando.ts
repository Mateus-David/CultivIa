import { useCallback, useState } from "react";
import { mensagemDeErro } from "@/lib/api";

// roda o comando e, se deu certo, chama aoConcluir pra tela buscar o estado novo
export function useComando(aoConcluir: () => void) {
  const [erro, setErro] = useState("");

  const executar = useCallback(
    async (acao: () => Promise<unknown>) => {
      try {
        await acao();
        setErro("");
        // espero um pouco pq a placa ainda tem que receber e confirmar
        setTimeout(aoConcluir, 500);
      } catch (e) {
        setErro(mensagemDeErro(e));
      }
    },
    [aoConcluir],
  );

  return { executar, erro };
}
