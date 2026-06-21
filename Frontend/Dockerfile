FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm install -g http-server
COPY --from=0 /app/dist/angualr-fronted/browser /app/dist

EXPOSE 4200
CMD ["http-server", "/app/dist", "-p", "4200", "-s"]
