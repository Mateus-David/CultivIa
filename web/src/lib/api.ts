// web/src/lib/api.ts — a ÚNICA porta de saída do site para o servidor.
//
// Caminho de cada pedido:
//   componente -> api.xxx() -> fetch("/api/...") -> Next.js (rewrites) -> FastAPI
//
// Os componentes nunca chamam fetch direto: usam o objeto `api` lá embaixo,
// que já sabe a rota, o método e o tipo da resposta.
import { token } from "./token";
import type { Envio, Estado, NomeAtuador, Setpoint } from "./types";

/** Erro com o código HTTP junto (401, 422, 503...). */
export class ErroApi extends Error {
  status: number;

  constructor(status: number, mensagem: string) {
    super(mensagem);
    this.status = status;
  }
}

type Opcoes = {
  method?: "GET" | "POST";
  corpo?: unknown;   // objeto que vira o JSON do corpo (só nos POST)
};

/** Faz a requisição e devolve o JSON já tipado como T. */
async function requisitar<T>(caminho: string, { method = "GET", corpo }: Opcoes = {}): Promise<T> {
  const resposta = await fetch(`/api${caminho}`, {
    method,
    headers: {
      // A API confere este cabeçalho (exige_token em api/app/auth.py)
      Authorization: `Bearer ${token.ler() ?? ""}`,
      ...(corpo !== undefined && { "Content-Type": "application/json" }),
    },
    body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
  });

  // 401 = token errado ou ausente: apaga e manda para o login
  // (a própria tela de login trata o erro, então lá não redireciona).
  if (resposta.status === 401) {
    token.apagar();
    if (window.location.pathname !== "/login") window.location.replace("/login");
    throw new ErroApi(401, "Token inválido");
  }

  if (!resposta.ok) {
    // O FastAPI explica o erro em {"detail": "..."}; usa isso se vier texto.
    const dados = await resposta.json().catch(() => null);
    const detalhe = typeof dados?.detail === "string" ? dados.detail : `Erro ${resposta.status}`;
    throw new ErroApi(resposta.status, detalhe);
  }

  return resposta.json() as Promise<T>;
}

/** Transforma qualquer erro numa frase para mostrar na tela. */
export function mensagemDeErro(erro: unknown): string {
  if (erro instanceof ErroApi) return erro.message;
  return "Sem conexão com a API";   // fetch falhou: rede fora ou servidor parado
}

type Ok = { ok: boolean };

// Uma função por rota de api/app/routes.py
export const api = {
  testarLogin: () => requisitar<Ok>("/login"),

  estado: () => requisitar<Estado>("/estado"),

  alternarAtuador: (nome: NomeAtuador, ligar: boolean) =>
    requisitar<Ok>(`/atuadores/${nome}`, { method: "POST", corpo: { estado: ligar } }),

  definirSetpoint: (setpoint: Setpoint) =>
    requisitar<Ok>("/setpoint", { method: "POST", corpo: setpoint }),

  configurarEnvio: (envio: Envio) =>
    requisitar<Ok>("/envio", { method: "POST", corpo: envio }),
};
