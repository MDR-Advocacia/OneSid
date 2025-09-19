from playwright.sync_api import Playwright, Browser

def iniciar_e_conectar(p: Playwright) -> Browser:
    """
    Inicia uma nova instância do navegador Chromium gerenciada pelo Playwright.
    Retorna o objeto 'browser' conectado.
    """
    print("▶️  Iniciando uma nova instância do navegador com Playwright...")
    try:
        # headless=False é necessário para que a extensão de login funcione.
        browser = p.chromium.launch(headless=False)
        print("✅ Navegador iniciado com sucesso!")
        return browser
    except Exception as e:
        print(f"❌ Falha ao iniciar o navegador com Playwright: {e}")
        raise

def fechar_navegador(browser: Browser):
    """
    Encerra a instância do navegador de forma limpa.
    """
    if browser and browser.is_connected():
        print("\n🏁 Fechando o navegador...")
        browser.close()
        print("✔️ Navegador fechado.")