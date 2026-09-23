// AtuadoresCard — uma linha com Toggle para cada atuador de ATUADORES.
import { Card } from "@/components/ui/Card";
import { Toggle } from "@/components/ui/Toggle";
import { ATUADORES } from "@/lib/atuadores";
import type { Dispositivo, NomeAtuador } from "@/lib/types";

type AtuadoresCardProps = {
  dispositivo: Dispositivo | null;
  habilitado: boolean;
  onAlternar: (nome: NomeAtuador, ligar: boolean) => void;
};

export function AtuadoresCard({ dispositivo, habilitado, onAlternar }: AtuadoresCardProps) {
  return (
    <Card titulo="Atuadores">
      {/* .map gera um elemento por item. `key` identifica cada um para o React. */}
      {ATUADORES.map(({ nome, rotulo, dica }) => {
        const ligado = dispositivo?.[nome] === 1;   // estado REAL, confirmado pela placa
        return (
          <div key={nome} className="flex items-center justify-between gap-2">
            <div>
              <div>{rotulo}</div>
              {dica && <small className="text-apagado">{dica}</small>}
            </div>
            <Toggle ligado={ligado} disabled={!habilitado} onAlternar={() => onAlternar(nome, !ligado)} />
          </div>
        );
      })}
    </Card>
  );
}
