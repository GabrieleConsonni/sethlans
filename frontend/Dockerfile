# syntax=docker/dockerfile:1
# --- Stage 1: build dei file statici con Vite ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
# Credenziali Nexus via BuildKit secret (id=npmrc): il token NON finisce
# nell'immagine. Build: docker compose build  (BuildKit attivo di default).
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm install

COPY . .

# URL del backend iniettato a build time (default: localhost dal browser dell'host).
# Sovrascrivibile a runtime anche dal campo in alto nell'interfaccia.
ARG VITE_API_URL=http://localhost:9955
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# --- Stage 2: servire la build con Nginx ---
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
