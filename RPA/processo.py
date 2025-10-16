import re
import logging
from playwright.sync_api import Page, TimeoutError

def _limpar_numero(numero_processo_bruto: str) -> str:
    """
    Função interna para remover todos os caracteres não numéricos 
    de uma string de número de processo.
    """
    return re.sub(r'\D', '', str(numero_processo_bruto))

def navegar_para_processo(page: Page, numero_processo: str, url_base: str):
    """
    Constrói a URL final do processo e navega até ela.
    """
    numero_limpo = _limpar_numero(numero_processo)
    url_final = f"{url_base}{numero_limpo}"
    
    logging.info(f"Navegando diretamente para o processo: {numero_processo} (URL: {url_final})")
    
    page.goto(url_final, wait_until="domcontentloaded")
    
    logging.info("Página de resultados do processo aberta.")

def acessar_detalhes(page: Page, num_processo: str):
    """
    Usa o número do processo para confirmar o carregamento da página e
    clica no botão 'Detalhar' da primeira correspondência encontrada.
    """
    iframe_selector = "#WIDGET_ID_1"
    
    try:
        logging.info("--- Acessando detalhes do processo ---")
        logging.info("1. Acessando o conteúdo (iframe)...")
        frame = page.frame_locator(iframe_selector)

        numero_processo_limpo = _limpar_numero(num_processo)

        logging.info(f"2. Aguardando a primeira linha do resultado para o processo '{numero_processo_limpo}'...")
        
        # Localiza a primeira linha (tr) que contém o número do processo
        primeira_linha = frame.locator(f"tr:has-text('{numero_processo_limpo}')").first
        primeira_linha.wait_for(state="visible", timeout=30000)
        
        logging.info("3. Linha de resultado visualizada. Localizando o botão 'Detalhar'...")
        # Procura o botão de detalhar APENAS DENTRO da primeira linha encontrada
        botao_detalhar = primeira_linha.locator('span[ng-click="editarProcesso(processo)"]')
        botao_detalhar.wait_for(state="visible")

        logging.info("4. Clicando em 'Detalhar'...")
        botao_detalhar.click()

        page.wait_for_load_state("networkidle")
        logging.info("✔️ SUCESSO! Página de detalhes carregada.")

    except Exception as e:
        logging.error(f"FALHA ao acessar detalhes do processo: {e}", exc_info=True)
        raise

def clicar_menu_subsidios(page: Page, num_processo: str):
    """
    Acessa o iframe da página de detalhes e clica no menu 'Subsídios'.
    """
    iframe_selector = "#WIDGET_ID_1"
    
    try:
        logging.info("--- Próxima etapa: Clicar no menu 'Subsídios' ---")
        
        logging.info("1. Acessando o iframe da página de detalhes...")
        frame = page.frame_locator(iframe_selector)
        
        logging.info("2. Aguardando a visualização do menu lateral (verificando por 'Dados do Processo')...")
        ancora_menu = frame.get_by_text("Dados do Processo", exact=True)
        ancora_menu.wait_for(state="visible")
        
        logging.info("3. Menu lateral visualizado. Localizando o item 'Subsídios'...")
        menu_subsidios = frame.get_by_text("Subsídios", exact=True)
        menu_subsidios.wait_for(state="visible")
        
        logging.info("4. Clicando em 'Subsídios'...")
        menu_subsidios.click()
        
        page.wait_for_load_state("networkidle")
        logging.info("✔️ SUCESSO! Menu 'Subsídios' clicado.")

    except Exception as e:
        logging.error(f"FALHA ao tentar clicar em 'Subsídios' para o processo {num_processo}.", exc_info=True)
        raise

def extrair_dados_subsidios(page: Page) -> list:
    """
    Na página de subsídios, localiza as colunas 'Item' e 'Estado' pelo nome
    e extrai os dados de cada linha da tabela.
    """
    iframe_selector = "#WIDGET_ID_1"
    dados_extraidos = []
    
    try:
        logging.info("--- Próxima etapa: Extrair dados da tabela de subsídios ---")
        frame = page.frame_locator(iframe_selector)
        
        logging.info("1. Aguardando a tabela carregar e localizando colunas...")
        
        frame.locator("thead").wait_for(state="visible", timeout=15000)
        
        headers = [h.upper() for h in frame.locator("thead th").all_text_contents()]
        
        try:
            item_index = headers.index('ITEM')
            estado_index = headers.index('ESTADO')
        except ValueError:
            logging.error("ERRO: Não foi possível encontrar as colunas 'Item' e 'Estado' na tabela.")
            return []

        logging.info(f"   - Coluna 'Item' encontrada na posição {item_index}.")
        logging.info(f"   - Coluna 'Estado' encontrada na posição {estado_index}.")

        # Verifica se existe alguma linha no corpo da tabela antes de prosseguir
        if frame.locator("tbody > tr").count() == 0:
            logging.info("Tabela de subsídios encontrada, mas está vazia.")
            return []

        frame.locator("tbody > tr").first.wait_for(state="visible", timeout=15000)
        
        logging.info("2. Tabela com dados visualizada. Extraindo informações...")
        linhas = frame.locator("tbody > tr").all()
        
        for linha in linhas:
            celulas = linha.locator("td").all()
            
            item = celulas[item_index].text_content().strip()
            estado = celulas[estado_index].text_content().strip()
            
            dados_extraidos.append({"item": item, "status": estado})
            logging.info(f"   - Item: {item} | Status: {estado}")
            
        logging.info(f"✔️ SUCESSO! {len(dados_extraidos)} registros extraídos.")
        return dados_extraidos

    except Exception as e:
        logging.warning(f"FALHA ao extrair dados dos subsídios: {e}")
        return []

