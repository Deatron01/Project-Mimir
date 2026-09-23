# Stage 1: build the React application
FROM node:20-alpine AS builder

# Build-time defaults. Every one of them can be overridden at runtime with MIMIR_* variables (see below).
ARG VITE_API_BASE_URL
ARG VITE_API_MODE=legacy
ARG VITE_USE_MOCKS=false
ARG VITE_PRIVACY_EMAIL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL VITE_API_MODE=$VITE_API_MODE VITE_USE_MOCKS=$VITE_USE_MOCKS VITE_PRIVACY_EMAIL=$VITE_PRIVACY_EMAIL

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run check && npm run build

# Stage 2: serve with Nginx on port 8501
FROM nginx:alpine
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/mimir.conf
# Runs before nginx starts: writes /config.json from MIMIR_API_BASE_URL, MIMIR_API_MODE, MIMIR_USE_MOCKS, MIMIR_PRIVACY_EMAIL.
COPY docker/40-mimir-config.sh /docker-entrypoint.d/40-mimir-config.sh
RUN chmod +x /docker-entrypoint.d/40-mimir-config.sh

EXPOSE 8501
CMD ["nginx", "-g", "daemon off;"]
