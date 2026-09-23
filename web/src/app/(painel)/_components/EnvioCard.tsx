// EnvioCard — intervalo entre leituras e pausar/retomar o envio.
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Slider } from "@/components/ui/Slider";
import { formatarSegundos } from "@/lib/formatar";
import type { Envio } from "@/lib/types";

type EnvioCardProps = {
  atual?: Envio;
  habilitado: boolean;
  onConfigurar: (envio: Envio) => void;
};

export function EnvioCard({ atual, habilitado, onConfigurar }: EnvioCardProps) {
  const [intervaloMs, setIntervaloMs] = useState(2000);

  return (
    <Card titulo="Envio de dados">
      <Slider
        rotulo="Intervalo"
        valor={intervaloMs}
        min={500}
        max={10000}
        passo={500}
        formatar={formatarSegundos}
        onChange={setIntervaloMs}
      />
      <div className="flex gap-2">
        <Button disabled={!habilitado} onClick={() => onConfigurar({ ativo: true, intervalo_ms: intervaloMs })}>
          Aplicar
        </Button>
        <Button
          variante="secundario"
          disabled={!habilitado}
          onClick={() => onConfigurar({ ativo: false, intervalo_ms: intervaloMs })}
        >
          Pausar
        </Button>
      </div>
      {atual && (
        <small className="text-apagado">
          {atual.ativo ? `Enviando a cada ${formatarSegundos(atual.intervalo_ms)}` : "Envio pausado"}
        </small>
      )}
    </Card>
  );
}
