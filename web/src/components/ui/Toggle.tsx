// Toggle — botão liga/desliga. Verde quando ligado.
//
// Ele NÃO guarda estado próprio: quem usa diz se está `ligado` e decide o
// que fazer no `onAlternar` (componente "controlado").
type ToggleProps = {
  ligado: boolean;
  disabled?: boolean;
  onAlternar: () => void;
};

export function Toggle({ ligado, disabled, onAlternar }: ToggleProps) {
  const cores = ligado ? "bg-verde text-verde-escuro" : "bg-borda text-texto";
  return (
    <button
      className={`min-w-25 cursor-pointer rounded-lg px-3.5 py-2 font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${cores}`}
      disabled={disabled}
      onClick={onAlternar}
    >
      {ligado ? "Ligado" : "Desligado"}
    </button>
  );
}
