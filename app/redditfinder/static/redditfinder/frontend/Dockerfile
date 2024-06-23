# Stage 1: Build the frontend
FROM node:latest AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

# Stage 2: Debug stage
FROM node:latest AS debug
WORKDIR /app
COPY --from=build /app /app
CMD ["tail", "-f", "/dev/null"]

# Stage 3: Serve the frontend
FROM nginx:alpine AS final

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
