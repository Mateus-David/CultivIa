import type { Estado, Setpoint } from "./types";

class ErroApi extends Error {}

type Opcoes = {
  method?: "GET" | "POST";
  corpo?: unknown;
};

async function requisitar<T>(caminho: string, { method = "GET", corpo }: Opcoes = {}): Promise<T> {
  const resposta = await fetch(`/api${caminho}`, {
    method,
    headers: corpo !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
  });

  if (!resposta.ok) {
    // o FastAPI manda o erro em {"detail": "..."}
    const dados = await resposta.json().catch(() => null);
    const detalhe = typeof dados?.detail === "string" ? dados.detail : `Erro ${resposta.status}`;
    throw new ErroApi(detalhe);
  }

  return resposta.json() as Promise<T>;
}

export function mensagemDeErro(erro: unknown): string {
  if (erro instanceof ErroApi) return erro.message;
  return "Sem conexão com a API";
}

type Ok = { ok: boolean };

export const api = {
  estado: () => requisitar<Estado>("/estado"),

  definirSetpoint: (setpoint: Setpoint) =>
    requisitar<Ok>("/setpoint", { method: "POST", corpo: setpoint }),
};
