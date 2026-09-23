// GrafanaCard — o dashboard do Grafana embutido num iframe.
//
// O React NÃO desenha esses gráficos: o navegador carrega a página do Grafana
// (porta 3000) aqui dentro. Os dados dela vêm do InfluxDB, que o Telegraf
// alimenta — caminho totalmente separado da API.
//
// O iframe só funciona por causa de GF_SECURITY_ALLOW_EMBEDDING e
// GF_AUTH_ANONYMOUS_* no serviço grafana do docker-compose.yml.
import { useEffect, useState } from "react";

/** Mesmo endereço (IP ou localhost) que abriu o site, porta 3000.
 *  kiosk = sem menus; theme=dark combina com o site; refresh=5s atualiza sozinho. */
function urlDoGrafana() {
  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:3000/d/cultivia-estufa?orgId=1&kiosk&theme=dark&refresh=5s`;
}

export function GrafanaCard() {
  // `window` só existe no navegador. Montar a URL dentro do useEffect
  // garante que isso nunca roda no servidor.
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => setUrl(urlDoGrafana()), []);

  return (
    <section className="mt-4 overflow-hidden rounded-xl border border-borda bg-cartao">
      {url && <iframe title="Dashboard Grafana" src={url} className="h-180 w-full border-0" />}
    </section>
  );
}
