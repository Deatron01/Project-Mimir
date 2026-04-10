# Stage 1: Build the React application
FROM node:18-alpine AS builder

# Átadjuk a build paramétereket
ARG VITE_WELLSPRING_URL
ARG VITE_RUNECARVER_URL
ARG VITE_BIFROST_INGEST_URL
ARG VITE_BIFROST_GENERATE_URL
ARG VITE_SKALD_URL

# Beállítjuk környezeti változónak, hogy a Vite lássa
ENV VITE_WELLSPRING_URL=$VITE_WELLSPRING_URL
ENV VITE_RUNECARVER_URL=$VITE_RUNECARVER_URL
ENV VITE_BIFROST_INGEST_URL=$VITE_BIFROST_INGEST_URL
ENV VITE_BIFROST_GENERATE_URL=$VITE_BIFROST_GENERATE_URL
ENV VITE_SKALD_URL=$VITE_SKALD_URL

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine
RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /app/dist /usr/share/nginx/html

# Készítünk egy saját Nginx konfigurációt, ami kezeli az aloldalakat (SPA routing) és a 8501-es portot
RUN echo "server { \
    listen 8501; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files \$uri \$uri/ /index.html; \
    } \
}" > /etc/nginx/conf.d/default.conf

EXPOSE 8501
CMD ["nginx", "-g", "daemon off;"]