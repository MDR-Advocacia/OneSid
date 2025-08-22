import time
import subprocess
from playwright.sync_api import Playwright, Browser
import config # Importa as configurações

# Variável para armazenar o processo do navegador
browser_process = None

def iniciar_e_conectar(p: Playwright) -> Browser:
    """
    Inicia o navegador executando o arquivo .bat e conecta-se a ele via Playwright.
    Retorna o objeto 'browser' conectado.
    """
    global browser_process
    
    print(f"▶️  Executando o script: {config.BAT_FILE_PATH}")
    browser_process = subprocess.Popen(
        str(config.BAT_FILE_PATH), 
        shell=True, 
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    print("    Aguardando o navegador iniciar...")

    for attempt in range(15): # Tenta se conectar por até 30 segundos
        try:
            time.sleep(2)
            print(f"    Tentativa de conexão nº {attempt + 1}...")
            browser = p.chromium.connect_over_cdp(config.CDP_ENDPOINT)
            print("✅ Conectado com sucesso ao navegador!")
            return browser
        except Exception:
            continue
    
    raise ConnectionError("Não foi possível conectar ao navegador após várias tentativas.")

def fechar_navegador():
    """
    Encerra o processo do navegador de forma limpa e automática.
    """
    global browser_process
    if browser_process:
        # A LINHA ABAIXO FOI REMOVIDA PARA TORNAR O PROCESSO 100% AUTOMÁTICO
        # input("\n... Pressione Enter para fechar o navegador e encerrar o script ...")
        
        # O comando TASKKILL é específico para Windows.
        print("\n🏁 Fechando o navegador automaticamente...")
        subprocess.run(f"TASKKILL /F /PID {browser_process.pid} /T", shell=True, capture_output=True)
        print("✔️ Navegador fechado. Fim da execução do RPA.")