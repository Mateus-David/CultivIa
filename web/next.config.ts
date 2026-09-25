import type { NextConfig } from "next";

// no Docker o Dockerfile define API_URL=http://api:8000, no npm run dev usa o localhost
const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",

  // /api/estado vira http://api:8000/estado, assim o navegador só fala com o next e não tem CORS
  async rewrites() {
    return [{ source: "/api/:caminho*", destination: `${API_URL}/:caminho*` }];
  },
};

export default nextConfig;
