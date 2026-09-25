import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Slider } from "@/components/ui/Slider";
import type { Setpoint } from "@/lib/types";

// mesmo valor inicial da placa
const PADRAO: Setpoint = { temperatura: 25, umidade: 50 };

type ParametrosCardProps = {
  naPlaca?: Setpoint;
  online: boolean;
  onEnviar: (alvo: Setpoint) => void;
};

export function ParametrosCard({ naPlaca, online, onEnviar }: ParametrosCardProps) {
  // enquanto for null os sliders mostram o que tá na placa,
  // depois que mexe fica o valor editado até clicar em enviar
  const [editado, setEditado] = useState<Setpoint | null>(null);
  const alvo = editado ?? naPlaca ?? PADRAO;

  return (
    <Card titulo="Parâmetros ideais">
      <div className="grid gap-4 sm:grid-cols-2">
        <Slider
          rotulo="Temperatura ideal"
          valor={alvo.temperatura}
          min={0}
          max={50}
          formatar={(v) => `${v} °C`}
          onChange={(temperatura) => setEditado({ ...alvo, temperatura })}
        />
        <Slider
          rotulo="Umidade ideal"
          valor={alvo.umidade}
          min={0}
          max={100}
          formatar={(v) => `${v} %`}
          onChange={(umidade) => setEditado({ ...alvo, umidade })}
        />
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        {/* dá pra enviar com a placa offline, o broker guarda e ela recebe quando conectar */}
        <Button onClick={() => onEnviar(alvo)}>Enviar para a placa</Button>
        <small className="text-apagado">
          <span className={online ? "text-verde" : "text-vermelho"}>●</span>{" "}
          {!online
            ? "Placa offline, ela recebe os valores quando conectar"
            : naPlaca
              ? `Placa usando ${naPlaca.temperatura} °C e ${naPlaca.umidade} %`
              : "Placa online"}
        </small>
      </div>
    </Card>
  );
}
