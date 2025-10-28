# 1. Imagem base com Python
FROM python:3.10-slim

# 2. Define o diretório de trabalho
WORKDIR /app

# 3. Copia o arquivo de dependências
COPY requirements.txt .

# 4. Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia o resto do código-fonte
COPY . .

# O comando CMD será definido no docker-compose, 
# pois este Dockerfile será usado por dois serviços (server e scheduler)