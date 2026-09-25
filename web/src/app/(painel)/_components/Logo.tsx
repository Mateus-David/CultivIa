// mesmo desenho do src/app/icon.svg (ícone da aba)
export function Logo() {
  return (
    <div className="flex items-center gap-3">
      <svg viewBox="0 0 32 32" className="size-10" aria-hidden="true">
        <rect width="32" height="32" rx="8" className="fill-verde" />
        <g className="fill-verde-escuro stroke-verde-escuro" strokeWidth="2.2" strokeLinecap="round">
          <path d="M16 25V15" fill="none" />
          <path d="M10 25h12" fill="none" />
          <path d="M16 19C16 14.5 12.5 11 7.5 11C7.5 15.5 11 19 16 19Z" stroke="none" />
          <path d="M16 15.5C16 10.5 19.5 7 24.5 7C24.5 12 21 15.5 16 15.5Z" stroke="none" />
        </g>
      </svg>
      <span className="text-2xl font-bold tracking-tight">
        Cultiv<span className="text-verde">Ia</span>
      </span>
    </div>
  );
}
