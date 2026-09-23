// web/src/lib/atuadores.ts — os atuadores que aparecem no painel.
//
// `nome` TEM que ser igual ao da API (NomeAtuador em api/app/schemas.py) e
// ao da placa (dict `atuadores` em firmware/esp32/main.py).
import type { NomeAtuador } from "./types";

type InfoAtuador = {
  nome: NomeAtuador;
  rotulo: string;
  dica?: string;
};

export const ATUADORES: InfoAtuador[] = [
  { nome: "ventilador", rotulo: "Ventilador", dica: "Reduz a temperatura" },
  { nome: "bomba", rotulo: "Bomba de irrigação", dica: "Aumenta a umidade (desliga sozinha em 60 s)" },
  { nome: "luz", rotulo: "Iluminação" },
];
