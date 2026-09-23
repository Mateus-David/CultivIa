# web/Dockerfile — imagem do site (serviço `web` do docker-compose.yml).
# Três estágios: só o último vai para produção; os outros são descartados.
# ATENÇÃO: comentário no Dockerfile só em linha PRÓPRIA (depois de um comando,
# um "# ..." seria lido como argumento).

# ---- 1. deps: instala as dependências (cacheado enquanto o lock não mudar) ----
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- 2. build: compila TypeScript/React/Tailwind -> .next/ ----
FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Para onde o Next.js repassa /api (ver next.config.ts). `api` = serviço do compose.
ENV API_URL=http://api:8000
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---- 3. produção: só o servidor standalone + arquivos estáticos ----
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
# Roda sem privilégios de root (o usuário `node` já existe na imagem)
USER node
EXPOSE 3000
CMD ["node", "server.js"]
