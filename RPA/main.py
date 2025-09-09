from playwright.sync_api import sync_playwright
import config
import navegador
import portal_bb
import processo
from bd import database

def executar_rpa(lista_processos: list):
    """
    Orquestra a execução do robô para uma lista de processos,
    atualizando o banco de dados com os resultados de cada um.
    """
    browser = None # Adiciona a variável no escopo mais alto
    try:
        with sync_playwright() as p:
            # A função agora retorna o browser, que precisamos guardar
            browser = navegador.iniciar_e_conectar(p)
            context = browser.new_context() # Usamos um novo contexto
            
            portal_page = portal_bb.fazer_login(context, config.EXTENSION_URL)
            
            for num_processo in lista_processos:
                print(f"\n--- INICIANDO CONSULTA PARA O PROCESSO: {num_processo} ---")
                try:
                    processo.navegar_para_processo(portal_page, num_processo, config.URL_BUSCA_PROCESSO)
                    # ... (resto do seu código aqui permanece o mesmo)
                except Exception as e:
                    print(f"!!!!!!!!!!!!!! ERRO AO PROCESSAR O PROCESSO {num_processo} !!!!!!!!!!!!!!")
                    print(f"Detalhes do erro: {e}")
                    print("Continuando para o próximo processo...")
                    continue

            print("\n✅ CONSULTA RPA FINALIZADA PARA TODOS OS PROCESSOS SOLICITADOS.")

    except Exception as e:
        print("\n========================= ERRO GERAL NO RPA =========================")
        print(f"Ocorreu uma falha crítica na automação: {e}")
        print("=====================================================================")
    finally:
        # Passamos a instância do browser para a função de fechar
        if browser:
            navegador.fechar_navegador(browser)

if __name__ == "__main__":
    print("Este script agora é projetado para ser chamado pelo server.py.")