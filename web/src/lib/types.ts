// mesmos formatos do api/app/schemas.py

export type Setpoint = {
  temperatura: number;
  umidade: number;
};

export type Sensores = {
  modo?: string;
  temperatura_simulada?: number;
  umidade_simulada?: number;
  temperatura_ideal?: number;
  umidade_ideal?: number;
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
