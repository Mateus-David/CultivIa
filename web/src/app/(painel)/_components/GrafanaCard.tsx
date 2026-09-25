import { useEffect, useState } from "react";

// pega o mesmo IP que abriu o site, só troca a porta pra 3000 (Grafana)
function urlDoGrafana() {
  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:3000/d/cultivia-estufa?orgId=1&kiosk&theme=dark&refresh=5s`;
}

// o iframe só funciona pq liguei o embedding e o acesso anônimo no docker-compose
export function GrafanaCard() {
  // window só existe no navegador, por isso monto a url no useEffect
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => setUrl(urlDoGrafana()), []);

  return (
    <section className="overflow-hidden rounded-xl border border-borda bg-cartao">
      {url && <iframe title="Dashboard Grafana" src={url} className="h-180 w-full border-0" />}
    </section>
  );
}
