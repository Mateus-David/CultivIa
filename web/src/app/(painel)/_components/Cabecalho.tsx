// Cabecalho — título, status da placa e botão Sair.
import { Button } from "@/components/ui/Button";
import { StatusPill } from "@/components/ui/StatusPill";

type CabecalhoProps = {
  online: boolean;
  onSair: () => void;
};

export function Cabecalho({ online, onSair }: CabecalhoProps) {
  return (
    <header className="flex items-center gap-3 py-4">
      {/* mr-auto empurra o resto para a direita */}
      <h1 className="mr-auto text-2xl font-bold">CultivIa</h1>
      <StatusPill ok={online}>{online ? "Placa online" : "Placa offline"}</StatusPill>
      <Button variante="link" onClick={onSair}>
        Sair
      </Button>
    </header>
  );
}
