// web/src/lib/types.ts — o FORMATO dos dados que vêm da API.
//
// Espelha api/app/schemas.py. Se mudar lá, mude aqui (o TypeScript então
// aponta todo lugar do site que precisa ser ajustado).

export type NomeAtuador = "ventilador" | "bomba" | "luz";

/** Alvos da simulação: para onde temperatura/umidade tendem. */
export type Setpoint = {
  temperatura: number;
  umidade: number;
};

/** Controle do envio de leituras da placa. */
export type Envio = {
  ativo: boolean;
  intervalo_ms: number;
};

/** Última mensagem de cultivia/sensores (a placa publica a cada ~2 s). */
export type Sensores = {
  modo?: string;
  temperatura_simulada?: number;
  umidade_simulada?: number;
};

/** Última mensagem de cultivia/estado ("como a placa está").
 *  Quando a placa cai, o Last Will troca tudo por só {"online": 0},
 *  por isso quase todos os campos são opcionais (`?`). */
export type Dispositivo = {
  online: 0 | 1;
  setpoint?: Setpoint;
  envio?: Envio;
} & Partial<Record<NomeAtuador, 0 | 1>>;   // ventilador?, bomba?, luz?

/** Resposta de GET /api/estado. */
export type Estado = {
  placa_online: boolean;
  mqtt: boolean;
  recebido_ha_s: number | null;
  sensores: Sensores | null;
  dispositivo: Dispositivo | null;
};
