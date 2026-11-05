// mesmos formatos do api/app/schemas.py

export type Setpoint = {
  temperatura: number;
  umidade: number;
};

// cada placa manda um pedaço: fans, bomba, umidade_ar e solo_raw só vêm da estufa
export type Sensores = {
  modo?: string;
  temperatura?: number;
  umidade?: number;
  temperatura_ideal?: number;
  umidade_ideal?: number;
  umidade_ar?: number;
  solo_raw?: number;
  fans?: number; // % de velocidade
  bomba?: number; // % de velocidade
};

// quando a placa cai o Last Will manda só {"online": 0}, por isso o setpoint é opcional
export type Dispositivo = {
  online: 0 | 1;
  setpoint?: Setpoint;
};

export type Estado = {
  placa_online: boolean;
  mqtt: boolean;
  recebido_ha_s: number | null;
  sensores: Sensores | null;
  dispositivo: Dispositivo | null;
};
