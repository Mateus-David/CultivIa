// LeiturasCard — temperatura e umidade atuais.
// Os dados vêm de cultivia/sensores (placa -> MQTT -> API -> aqui).
import { Card } from "@/components/ui/Card";
import { Metrica } from "@/components/ui/Metrica";
import { formatarMedida } from "@/lib/formatar";
import type { Sensores } from "@/lib/types";

type LeiturasCardProps = {
  sensores: Sensores | null;
};

export function LeiturasCard({ sensores }: LeiturasCardProps) {
  return (
    <Card>
      <div className="flex flex-1 items-center justify-around">
        {/* `?.` = "se existir": evita erro enquanto sensores ainda é null */}
        <Metrica rotulo="Temperatura" valor={formatarMedida(sensores?.temperatura_simulada, 1, "°C")} />
        <Metrica rotulo="Umidade" valor={formatarMedida(sensores?.umidade_simulada, 0, "%")} />
      </div>
    </Card>
  );
}
