// Metrica — um número grande com um rótulo pequeno em cima.
type MetricaProps = {
  rotulo: string;
  valor: string;
};

export function Metrica({ rotulo, valor }: MetricaProps) {
  return (
    <div className="flex flex-col items-center">
      <span className="text-sm text-apagado">{rotulo}</span>
      <strong className="text-3xl tabular-nums">{valor}</strong>
    </div>
  );
}
