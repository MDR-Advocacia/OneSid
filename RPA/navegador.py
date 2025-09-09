from playwright.sync_api import Playwright, Browser
import subprocess

# Variável para armazenar o processo do navegador
browser_process = None

def iniciar_e_conectar(p: Playwright) -> Browser:
    """
    Inicia um navegador Chromium em modo headless (sem interface gráfica)
    e retorna o objeto 'browser' conectado.
    """
    print("▶️  Iniciando o navegador Chromium em modo headless...")
    
    # Instala as dependências do sistema para o navegador, se necessário (importante para o servidor)
    try:
        subprocess.run(["playwright", "install-deps"], check=True)
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível rodar 'playwright install-deps'. Isso é normal no Windows. Erro: {e}")

    browser = p.chromium.launch(headless=True)
    print("✅ Navegador iniciado com sucesso!")
    return browser

def fechar_navegador(browser: Browser):
    """
    Encerra a instância do navegador de forma limpa.
    """
    if browser:
        print("\n🏁 Fechando o navegador...")
        browser.close()
        print("✔️ Navegador fechado. Fim da execução do RPA.")