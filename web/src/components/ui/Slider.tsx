type SliderProps = {
  rotulo: string;
  valor: number;
  min: number;
  max: number;
  formatar?: (valor: number) => string;
  onChange: (valor: number) => void;
};

export function Slider({ rotulo, valor, min, max, formatar = String, onChange }: SliderProps) {
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
        value={valor}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}
