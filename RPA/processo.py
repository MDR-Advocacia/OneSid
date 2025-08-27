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

def acessar_detalhes(page: Page, num_processo: str):
    """
    Usa o número do processo para confirmar o carregamento da página e
    clica diretamente no elemento de 'Detalhar'.
    """
    iframe_selector = "#WIDGET_ID_1"
    
    try:
        print("\n--- Acessando detalhes do processo ---")
        print("1. Acessando o conteúdo (iframe)...")
        frame = page.frame_locator(iframe_selector)

        numero_processo_limpo = _limpar_numero(num_processo)

        print(f"2. Aguardando a visualização do dado: '{numero_processo_limpo}'...")
        dado_carregado = frame.locator(f"span.ng-binding:has-text('{numero_processo_limpo}')")
        dado_carregado.wait_for(state="visible")
        
        print("3. Dados visualizados. Localizando o botão 'Detalhar'...")
        botao_detalhar = frame.locator('span[ng-click="editarProcesso(processo)"]').first
        botao_detalhar.wait_for(state="visible")

        print("4. Clicando em 'Detalhar'...")
        botao_detalhar.click()

        page.wait_for_load_state("networkidle")
        print("\n✔️ SUCESSO! Página de detalhes carregada.")

    except Exception as e:
        print(f"\n❌ FALHA ao acessar detalhes do processo: {e}")
        raise

def clicar_menu_subsidios(page: Page, num_processo: str):
    """
    Acessa o iframe da página de detalhes e clica no menu 'Subsídios'.
    """
    iframe_selector = "#WIDGET_ID_1"
    
    try:
        print("\n--- Próxima etapa: Clicar no menu 'Subsídios' ---")
        
        print("1. Acessando o iframe da página de detalhes...")
        frame = page.frame_locator(iframe_selector)
        
        print("2. Aguardando a visualização do menu lateral (verificando por 'Dados do Processo')...")
        ancora_menu = frame.get_by_text("Dados do Processo", exact=True)
        ancora_menu.wait_for(state="visible")
        
        print("3. Menu lateral visualizado. Localizando o item 'Subsídios'...")
        menu_subsidios = frame.get_by_text("Subsídios", exact=True)
        menu_subsidios.wait_for(state="visible")
        
        print("4. Clicando em 'Subsídios'...")
        menu_subsidios.click()
        
        page.wait_for_load_state("networkidle")
        print("✔️ SUCESSO! Menu 'Subsídios' clicado.")

    except Exception as e:
        print(f"\n❌ FALHA ao tentar clicar em 'Subsídios': {e}")
        print("   - O robô não conseguiu visualizar o menu 'Dados do Processo' ou 'Subsídios' dentro do iframe.")
        raise

def extrair_dados_subsidios(page: Page) -> list:
    """
    Na página de subsídios, localiza as colunas 'Item' e 'Estado' pelo nome
    e extrai os dados de cada linha da tabela.
    """
    iframe_selector = "#WIDGET_ID_1"
    dados_extraidos = []
    
    try:
        print("\n--- Próxima etapa: Extrair dados da tabela de subsídios ---")
        frame = page.frame_locator(iframe_selector)
        
        print("2. Aguardando a tabela carregar e localizando colunas...")
        
        frame.locator("thead").wait_for(state="visible")
        
        headers = [h.upper() for h in frame.locator("thead th").all_text_contents()]
        
        try:
            item_index = headers.index('ITEM')
            estado_index = headers.index('ESTADO')
        except ValueError:
            print("❌ ERRO: Não foi possível encontrar as colunas 'Item' e 'Estado' na tabela.")
            return []

        print(f"   - Coluna 'Item' encontrada na posição {item_index}.")
        print(f"   - Coluna 'Estado' encontrada na posição {estado_index}.")

        frame.locator("tbody > tr").first.wait_for(state="visible", timeout=15000)
        
        print("3. Tabela com dados visualizada. Extraindo informações...")
        linhas = frame.locator("tbody > tr").all()
        
        for linha in linhas:
            celulas = linha.locator("td").all()
            
            item = celulas[item_index].text_content().strip()
            estado = celulas[estado_index].text_content().strip()
            
            dados_extraidos.append({"item": item, "status": estado})
            print(f"   - Item: {item} | Status: {estado}")
            
        print(f"✔️ SUCESSO! {len(dados_extraidos)} registros extraídos.")
        return dados_extraidos

    except Exception as e:
        print(f"❌ FALHA ao extrair dados dos subsídios: {e}")
        return []