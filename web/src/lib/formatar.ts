// web/src/lib/formatar.ts — transforma números em texto para a tela.

/** 25.345 -> "25.3 °C"; valor ausente -> "—". */
export function formatarMedida(valor: number | undefined, casas: number, unidade: string): string {
  return valor == null ? "—" : `${valor.toFixed(casas)} ${unidade}`;
}

/** 2500 -> "2.5 s" */
export function formatarSegundos(ms: number): string {
  return `${(ms / 1000).toFixed(1)} s`;
}
