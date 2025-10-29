import time
import subprocess
from playwright.sync_api import Playwright, Browser
import config  # Importa as configurações
import re      # <-- ADICIONADO (Necessário para a correção)
import sys     # <-- ADICIONADO (Necessário para a correção)

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
    Encerra o processo do navegador de forma limpa e automática,
    matando o processo do Chrome pela porta de depuração.
    """
    print("\n🏁 Iniciando rotina de fechamento do navegador...")

    # 1. Extrai a porta do endpoint de configuração
    port_match = re.search(r':(\d+)$', config.CDP_ENDPOINT)
    if not port_match:
        print(f"     Aviso: Não foi possível extrair a porta do CDP_ENDPOINT: {config.CDP_ENDPOINT}")
        print("     O navegador não pode ser fechado pela porta.")
        return
    
    port = port_match.group(1)
    print(f"     Procurando e finalizando o processo do Chrome na porta {port}...")

    # 2. Lógica para encontrar e matar o PID (Obriga o Chrome a fechar)
    try:
        if sys.platform == "win32":
            # Comando para encontrar o PID que está usando a porta
            cmd_find_pid = f"netstat -ano -p TCP | findstr :{port}"
            result = subprocess.run(cmd_find_pid, shell=True, capture_output=True, text=True, check=False)
            output = result.stdout.strip()

            if not output:
                print(f"     Nenhum processo encontrado na porta {port}.")
            else:
                # Tenta extrair o PID (é o último número na linha)
                pid_match = re.search(r'(\d+)$', output.splitlines()[0])
                if pid_match:
                    pid = pid_match.group(1)
                    print(f"     Encontrado processo (PID: {pid}) na porta {port}. Finalizando...")
                    # Comando para matar o PID encontrado
                    subprocess.run(f"TASKKILL /F /PID {pid} /T", shell=True, check=False, capture_output=True)
                    print(f"✔️ Processo {pid} (Chrome) finalizado.")
                else:
                    print(f"     Não foi possível extrair o PID da saída do netstat: {output}")
        else:
            # Lógica para Linux/Mac
            subprocess.run(f"lsof -t -i:{port} | xargs kill -9", shell=True, check=False, capture_output=True)
            print(f"✔️ Comando de finalização (Linux/Mac) executado para a porta {port}.")

    except Exception as e_kill:
        print(f"     Aviso: Falha ao tentar finalizar o processo da porta {port}: {e_kill}")

    print("--- Rotina de fechamento concluída. Fim da execução do RPA. ---")