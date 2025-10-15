# Estágio 1: Build da aplicação React
FROM node:18-alpine as build

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de manifesto do projeto
COPY package.json ./
COPY package-lock.json ./

# Instala as dependências
RUN npm install

# Copia o restante dos arquivos do projeto
COPY . .

# Builda a aplicação para produção
RUN npm run build

# Estágio 2: Servir a aplicação com Nginx
FROM nginx:stable-alpine

# Copia os arquivos de build do estágio anterior para o diretório padrão do Nginx
COPY --from=build /app/build /usr/share/nginx/html

# Expõe a porta 80
EXPOSE 80

# Comando para iniciar o Nginx
CMD ["nginx", "-g", "daemon off;"]