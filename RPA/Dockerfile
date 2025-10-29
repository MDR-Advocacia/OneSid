# 1. Use a imagem oficial do Python como base
FROM python:3.11-slim

# 2. Instala o Node.js e o npm (necessários para o Playwright)
RUN apt-get update && apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# 3. Define o diretório de trabalho no contêiner
WORKDIR /app

# 4. Copia o arquivo de dependências
# (Ele busca o requirements.txt na pasta RPA, que é o contexto)
COPY requirements.txt .

# 5. Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# 6. Instala os navegadores necessários para o Playwright
RUN playwright install --with-deps

# 7. Copia o restante do código da pasta RPA para o /app
COPY . .

# 8. Expõe a porta que a aplicação Flask usa
EXPOSE 5000

# O CMD não é necessário aqui, pois o seu docker-compose.yml
# já define o comando: "command: python server.py"