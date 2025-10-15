# Use a imagem oficial do Python como base
FROM python:3.11-slim

# Instala o Node.js e o npm para instalar o playwright
RUN apt-get update && apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Copia os arquivos de dependências
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Instala os navegadores necessários para o Playwright
RUN playwright install --with-deps

# Copia o restante do código da aplicação
COPY . .

# Expõe a porta que a aplicação Flask usa
EXPOSE 5000

# Comando para iniciar o servidor Flask quando o contêiner for executado
CMD ["python", "server.py"]