import sys
import os
from playwright.sync_api import sync_playwright
from RPA import navegador, portal_bb, processo, config
from bd import database

caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)

def executar_rpa(lista_processos: list, funcao_de_atualizacao=database.atualizar_status_para_usuarios):
    print("--- INICIANDO EXECUÇÃO DO RPA ---")
    browser = None
    try:
        with sync_playwright() as p:
            browser = navegador.iniciar_e_conectar(p)
            if not browser:
                print("❌ Falha ao iniciar o navegador. Abortando.")
                return

            context = browser.contexts[0]
            
            print("1. Realizando login no portal...")
            # CORREÇÃO: Passa o 'context' para a função de login e recebe a 'page' de volta.
            portal_page = portal_bb.fazer_login(context, config.EXTENSION_URL)
            if not portal_page:
                print("❌ Falha no login. Verifique as credenciais ou a página.")
                return # Encerra se o login falhar
            print("✔️ Login realizado com sucesso.")

            print(f"2. Iniciando consulta para {len(lista_processos)} processo(s).")
            for num_processo in lista_processos:
                try:
                    # --- VERIFICAÇÃO DE SESSÃO ADICIONADA ---
                    # Garante que o robô está logado antes de processar cada item.
                    portal_page = portal_bb.verificar_e_renovar_sessao(portal_page, context, config.EXTENSION_URL)
                    # -----------------------------------------

                    print(f"\n   --- Processando: {num_processo} ---")
                    print(f"    a. Navegando para a página do processo...")
                    processo.navegar_para_processo(portal_page, num_processo, config.URL_BUSCA_PROCESSO)
                    
                    print(f"    b. Acessando detalhes e subsídios...")
                    processo.acessar_detalhes(portal_page, num_processo)
                    processo.clicar_menu_subsidios(portal_page, num_processo)
                    
                    print(f"    c. Extraindo dados da tabela...")
                    dados_subsidios_do_processo = processo.extrair_dados_subsidios(portal_page)
                    
                    if dados_subsidios_do_processo:
                        print(f"    d. Encontrados {len(dados_subsidios_do_processo)} subsídios. Atualizando banco de dados...")
                        funcao_de_atualizacao(num_processo, dados_subsidios_do_processo)
                        print(f"    ✔️ Banco de dados atualizado para o processo {num_processo}.")
                    else:
                        print(f"    d. Nenhum subsídio encontrado para {num_processo}.")

                except Exception as e:
                    print(f"!!!!!!!!!!!!!! ERRO AO PROCESSAR {num_processo} !!!!!!!!!!!!!!")
                    print(f"Detalhes: {e}")
                    continue

            print("\n✅ CONSULTA RPA FINALIZADA.")

    except Exception as e:
        print("\n========================= ERRO GERAL NO RPA =========================")
        print(f"Ocorreu uma falha crítica na automação: {e}")
    finally:
        if browser:
            print("3. Fechando navegador...")
            navegador.fechar_navegador()
        print("--- EXECUÇÃO DO RPA FINALIZADA ---")

if __name__ == "__main__":
    print("Este script é projetado para ser chamado pelo server.py ou scheduler.py.")