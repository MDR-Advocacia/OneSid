import re
from playwright.sync_api import Page, TimeoutError

def _limpar_numero(numero_processo_bruto: str) -> str:
    """
    Função interna para remover todos os caracteres não numéricos 
    de uma string de número de processo.
    """
    return re.sub(r'\D', '', numero_processo_bruto)

def navegar_para_processo(page: Page, numero_processo: str, url_base: str):
    """
    Constrói a URL final do processo e navega até ela.
    """
    numero_limpo = _limpar_numero(numero_processo)
    url_final = f"{url_base}{numero_limpo}"
    
    print(f"\n🔎 Navegando diretamente para o processo: {numero_processo}")
    print(f"    URL: {url_final}")
    
    page.goto(url_final, wait_until="domcontentloaded")
    
    print("✔️ Página de resultados do processo aberta.")

def acessar_detalhes(page: Page):
    """
    IMitando o vídeo: Acessa o iframe, passa o mouse sobre a linha do processo
    para revelar o ícone de 'informações' e clica nele.
    """
    iframe_selector = "#WIDGET_ID_1"
    
    try:
        print("\n--- Imitando o vídeo ---")
        print("1. Acessando o conteúdo (iframe)...")
        frame = page.frame_locator(iframe_selector)

        print("2. Localizando a linha do processo...")
        linha_processo = frame.locator("tr.pointer-cursor").first
        linha_processo.wait_for(state="visible", timeout=30000)

        print("3. Passando o mouse sobre a linha para revelar as ações...")
        linha_processo.hover()

        # Seletor para o ÍCONE, conforme mostrado no vídeo.
        icone_info = frame.locator("i.mi-info").first
        
        print("4. Aguardando o ÍCONE de informações aparecer...")
        icone_info.wait_for(state="visible", timeout=5000)

        print("5. Clicando no ÍCONE...")
        icone_info.click()

        page.wait_for_load_state("networkidle", timeout=30000)
        print("\n✔️ SUCESSO! Ação do vídeo concluída. Página de detalhes carregada.")

    except Exception as e:
        print("\n❌ FALHA. Mesmo imitando o vídeo, a automação não conseguiu interagir com o elemento.")
        raise e