FROM node:latest AS build

WORKDIR /app

COPY package*.json ./

RUN npm install

RUN npm install -D tailwindcss postcss autoprefixer @iconify/react @iconify-icons/fa

RUN npx tailwindcss init -p

COPY . .

RUN npm run build

RUN ls -la /app/dist

FROM nginx:alpine AS final

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
