# 1. Imagem base com Node.js
FROM node:18-alpine

# 2. Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# 3. Copia os arquivos de definição de pacotes
COPY package.json package-lock.json ./

# 4. Instala as dependências
RUN npm install

# 5. Copia o resto do código-fonte do seu app
COPY . .

# 6. Expõe a porta que o React usa (geralmente 3000)
EXPOSE 3000

# 7. O comando para iniciar o app (o seu npm start)
CMD ["npm", "start"]