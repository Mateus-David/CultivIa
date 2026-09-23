// web/next.config.ts — configuração do Next.js.
import type { NextConfig } from "next";

// Endereço da API (FastAPI). Lido na hora da BUILD:
//   - Docker: o web/Dockerfile define API_URL=http://api:8000 (nome do serviço)
//   - `npm run dev`: não há API_URL, então usa a porta 8000 publicada no host
const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Gera um servidor Node enxuto em .next/standalone (é o que roda no Docker).
  output: "standalone",

  // O navegador só conversa com o Next.js. Pedidos para /api/... são
  // repassados para a API, sem o prefixo /api:
  //   navegador GET /api/estado  ->  Next.js  ->  http://api:8000/estado
  // Como tudo sai do mesmo endereço, não há problema de CORS.
  async rewrites() {
    return [{ source: "/api/:caminho*", destination: `${API_URL}/:caminho*` }];
  },
};

export default nextConfig;
