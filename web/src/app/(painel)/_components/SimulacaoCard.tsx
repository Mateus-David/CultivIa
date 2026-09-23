// SimulacaoCard — escolhe os alvos de temperatura/umidade da simulação.
//
// Os sliders mexem só no estado LOCAL (`alvo`); nada vai para a placa até
// clicar em "Aplicar alvos".
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Slider } from "@/components/ui/Slider";
import type { Setpoint } from "@/lib/types";

type SimulacaoCardProps = {
  atual?: Setpoint;   // o que a placa está usando de fato
  habilitado: boolean;
  onAplicar: (alvo: Setpoint) => void;
};

export function SimulacaoCard({ atual, habilitado, onAplicar }: SimulacaoCardProps) {
  const [alvo, setAlvo] = useState<Setpoint>({ temperatura: 25, umidade: 60 });

  return (
    <Card titulo="Simulação">
      <Slider
        rotulo="Temperatura alvo"
        valor={alvo.temperatura}
        min={0}
        max={40}
        formatar={(v) => `${v} °C`}
        // `...alvo` copia os campos atuais; só a temperatura muda
        onChange={(temperatura) => setAlvo({ ...alvo, temperatura })}
      />
      <Slider
        rotulo="Umidade alvo"
        valor={alvo.umidade}
        min={0}
        max={100}
        formatar={(v) => `${v} %`}
        onChange={(umidade) => setAlvo({ ...alvo, umidade })}
      />
      <Button disabled={!habilitado} onClick={() => onAplicar(alvo)}>
        Aplicar alvos
      </Button>
      {atual && (
        <small className="text-apagado">
          Atual na placa: {atual.temperatura} °C / {atual.umidade} %
        </small>
      )}
    </Card>
  );
}
