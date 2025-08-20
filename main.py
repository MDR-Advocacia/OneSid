from playwright.sync_api import sync_playwright
import config
import navegador
import portal_bb
import processo

def run():
    """
    Função principal que orquestra a execução do robô.
    """
    lista_processos = ["0803535-15.2025.8.20.5103"]

    try:
        with sync_playwright() as p:
            browser = navegador.iniciar_e_conectar(p)
            context = browser.contexts[0]
            
            portal_page = portal_bb.fazer_login(context, config.EXTENSION_URL)
            
            for num_processo in lista_processos:
                processo.navegar_para_processo(portal_page, num_processo, config.URL_BUSCA_PROCESSO)
                
                # Etapa 1: Acessar detalhes (já funcionando)
                processo.acessar_detalhes(portal_page, num_processo)
                
                # --- LINHA MODIFICADA ---
                # Etapa 2: Clicar em subsídios, passando o número do processo para confirmação
                processo.clicar_menu_subsidios(portal_page, num_processo)
                # -------------------------
                
            print("\n✅ TODOS OS PROCESSOS FORAM CONSULTADOS.")

    except Exception as e:
        print("\n========================= ERRO =========================")
        print(f"Ocorreu uma falha na automação: {e}")
        print("========================================================")
    finally:
        navegador.fechar_navegador()


if __name__ == "__main__":
    run()