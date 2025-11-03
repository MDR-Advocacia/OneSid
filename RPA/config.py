# Em: RPA/config.py
import os
from pathlib import Path

# --- LEITURA DAS VARIÁVEIS DE AMBIENTE VINDAS DO DOCKER ---
# Lê o IP do host (definido no .env e passado pelo docker-compose)
# Se a variável não existir, ele usa '127.0.0.1' como fallback
HOST_IP = os.environ.get('HOST_IP', '127.0.0.1')

# Lê a origem do frontend (também do .env) para as permissões de CORS
# O server.py vai importar esta variável
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://localhost:3000')


# --- CONFIGURAÇÕES DE CONEXÃO ---
EXTENSION_URL = "chrome-extension://lnidijeaekolpfeckelhkomndglcglhh/index.html"
CDP_ENDPOINT = "http://localhost:9222"

# --- CAMINHOS DE ARQUIVOS ---
BAT_FILE_PATH = Path(__file__).resolve().parent / "abrir_chrome.bat"

# --- URLs DA APLICAÇÃO (AGORA DINÂMICAS) ---
URL_BUSCA_PROCESSO = "https://juridico.bb.com.br/paj/juridico/v2?app=processoConsultaRapidoTomboApp&numeroTombo="

# URL da API do "scheduler_api.py" (a que estava no api_client.py)
API_TASKS_BATCH_URL = f"http://{HOST_IP}:8000/api/v1/tasks/batch-create"

# URL base da API do "server.py" (a que o frontend usa)
API_SERVER_BASE_URL = f"http://{HOST_IP}:5000/api"