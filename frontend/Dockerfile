# Stage 1: build the React application
FROM node:20-alpine AS builder

# Optional: API gateway base URL baked into the build (defaults are in src/config.js).
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run check && npm run build

# Stage 2: serve with Nginx
FROM nginx:alpine
RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /app/dist /usr/share/nginx/html

# SPA routing on port 8501
RUN printf 'server {\n  listen 8501;\n  location / {\n    root /usr/share/nginx/html;\n    index index.html;\n    try_files $uri $uri/ /index.html;\n  }\n}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 8501
CMD ["nginx", "-g", "daemon off;"]
