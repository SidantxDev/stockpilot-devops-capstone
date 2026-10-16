# syntax=docker/dockerfile:1

# ---- Stage 1: build the React app with Node ---------------------------------
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
# The git commit SHA is shown in the UI sidebar so you can see which build is live.
ARG APP_VERSION=dev
ENV VITE_APP_VERSION=$APP_VERSION
RUN npm run build

# ---- Stage 2: serve static files with unprivileged Nginx ---------------------
# nginx-unprivileged runs as uid 101 and listens on 8080 (no root needed).
FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime

LABEL org.opencontainers.image.title="stockpilot-frontend" \
      org.opencontainers.image.description="StockPilot inventory dashboard (React + Nginx)" \
      org.opencontainers.image.licenses="MIT"

# Apply Alpine security fixes published after the base image was built.
USER root
RUN apk upgrade --no-cache
USER 101

ENV BACKEND_URL=http://backend:8000

COPY --chown=101:101 nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build --chown=101:101 /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
