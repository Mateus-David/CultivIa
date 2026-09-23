// Slider — controle deslizante com rótulo e valor formatado.
//
//   <Slider rotulo="Umidade alvo" valor={60} min={0} max={100}
//           formatar={(v) => `${v} %`} onChange={setUmidade} />
type SliderProps = {
  rotulo: string;
  valor: number;
  min: number;
  max: number;
  passo?: number;
  formatar?: (valor: number) => string;
  onChange: (valor: number) => void;
};

export function Slider({ rotulo, valor, min, max, passo = 1, formatar = String, onChange }: SliderProps) {
  return (
    <label className="flex flex-col gap-1.5">
      <span>
        {rotulo}: <b>{formatar(valor)}</b>
      </span>
      <input
        type="range"
        className="w-full accent-verde"
        min={min}
        max={max}
        step={passo}
        value={valor}
        // o valor do input vem como texto: Number() converte
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}
