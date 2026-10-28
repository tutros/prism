FROM node:22-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci


FROM deps AS build

# Empty base makes the SPA call /api relative to its own origin, which nginx proxies
# to the backend. Override at build time for a split deployment:
#   docker compose build --build-arg VITE_API_BASE=https://api.example.com
ARG VITE_API_BASE=
ENV VITE_API_BASE=$VITE_API_BASE

COPY . .
RUN npm run build


FROM nginx:alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
