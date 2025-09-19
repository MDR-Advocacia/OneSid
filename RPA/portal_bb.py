from playwright.sync_api import BrowserContext, Page, TimeoutError

def fazer_login(context: BrowserContext, url_extensao: str) -> Page:
    """
    Abre a extensão, realiza a busca pelo sistema, clica para fazer o login
    e aguarda a página principal do portal carregar completamente.
    """
    try:
        print("🚀 Iniciando o processo de login pela extensão...")
        extension_page = context.new_page()
        extension_page.goto(url_extensao)
        extension_page.wait_for_load_state("domcontentloaded")

        print("    - Localizando o campo de busca na extensão...")
        search_input = extension_page.get_by_placeholder("Digite ou selecione um sistema pra acessar")
        search_input.wait_for(state="visible", timeout=10000)

        print("    - Pesquisando por 'banco do'...")
        search_input.fill("banco do")

        print("🖱️  Clicando no item de menu 'Banco do Brasil - Intranet'...")
        login_button = extension_page.locator(
            'div[role="menuitem"]:not([disabled])', 
            has_text="Banco do Brasil - Intranet"
        ).first
        login_button.click(timeout=10000)

        print("    - Clicando no botão de confirmação 'ACESSAR'...")
        # Espera a nova página (o portal) ser aberta como resultado do clique.
        with context.expect_page() as new_page_info:
            extension_page.get_by_role("button", name="ACESSAR").click(timeout=10000)
        portal_page = new_page_info.value
        
        print("    - Aguardando a página inicial do portal carregar...")
        
        # --- NOVA LÓGICA DE VERIFICAÇÃO DE LOGIN ADICIONADA ---
        # Usamos o seletor de ID, que é o mais robusto e específico.
        elemento_de_confirmacao = portal_page.locator("#aPaginaInicial")
        
        # O robô agora espera ativamente até que o link "Página Inicial" esteja visível.
        elemento_de_confirmacao.wait_for(state="visible", timeout=90000)
        
        print("    - Verificação de login bem-sucedida! Link 'Página inicial' encontrado.")
        # --------------------------------------------------------

        print("✔️  Login confirmado! A página do portal foi carregada com sucesso.")
        extension_page.close()
        
        return portal_page

    except TimeoutError as e:
        print("\n❌ FALHA no processo de login (Timeout).")
        print("   - O robô não conseguiu encontrar um elemento da extensão ou da página do portal a tempo.")
        raise e
    except Exception as e:
        print(f"\n❌ FALHA inesperada durante o login: {e}")
        raise e

def verificar_e_renovar_sessao(page: Page, context: BrowserContext, url_extensao: str) -> Page:
    """
    Verifica se a sessão do usuário ainda está ativa. Se não estiver,
    tenta fazer o login novamente.
    """
    try:
        # Verifica a presença do elemento que confirma o login, com um timeout curto.
        page.locator("#aPaginaInicial").wait_for(state="visible", timeout=5000)
        print("✔️ Sessão ativa. Continuando o processo.")
        return page
    except TimeoutError:
        print("\n⚠️ Sessão expirada ou inválida! Iniciando processo de re-login...")
        try:
            # Fecha a página antiga para evitar conflitos
            if not page.is_closed():
                page.close()

            # Chama a função de login para obter uma nova página/sessão
            nova_page = fazer_login(context, url_extensao)
            print("✔️ Re-login realizado com sucesso!")
            return nova_page
        except Exception as e:
            print(f"\n❌ FALHA CRÍTICA no processo de re-login: {e}")
            raise  # Propaga a exceção para que o RPA principal possa parar.