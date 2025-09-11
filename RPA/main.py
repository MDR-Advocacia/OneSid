import sys
import os
from playwright.sync_api import sync_playwright
from RPA import navegador, portal_bb, processo, config
from bd import database

# Adiciona o diretório raiz ao path para encontrar o módulo 'bd'
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)

# ==================================================================
#               PRIMEIRA ALTERAÇÃO (Assinatura da função)
# ==================================================================
# A função agora aceita o segundo argumento para ser flexível
def executar_rpa(lista_processos: list, funcao_de_atualizacao=database.atualizar_status_para_usuarios):
    """
    Orquestra a execução do robô para uma lista de processos,
    atualizando o banco de dados com os resultados de cada um.
    """
# ==================================================================
    try:
        with sync_playwright() as p:
            # Mantivemos a sua lógica original de inicialização
            browser = navegador.iniciar_e_conectar(p)
            context = browser.contexts[0]
            
            # Mantivemos a sua chamada original e correta para 'fazer_login'
            portal_page = portal_bb.fazer_login(context, config.EXTENSION_URL)
            
            for num_processo in lista_processos:
                print(f"\n--- INICIANDO CONSULTA PARA O PROCESSO: {num_processo} ---")
                try:
                    processo.navegar_para_processo(portal_page, num_processo, config.URL_BUSCA_PROCESSO)
                    processo.acessar_detalhes(portal_page, num_processo)
                    processo.clicar_menu_subsidios(portal_page, num_processo)
                    
                    dados_subsidios_do_processo = processo.extrair_dados_subsidios(portal_page)
                    
                    if dados_subsidios_do_processo:
                        # ==================================================================
                        #               SEGUNDA ALTERAÇÃO (Chamada da função)
                        # ==================================================================
                        # Usamos a função que foi passada como argumento
                        funcao_de_atualizacao(num_processo, dados_subsidios_do_processo)
                        # ==================================================================
                    else:
                        print(f"AVISO: Nenhum subsídio encontrado para o processo {num_processo}. Status não atualizado.")

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
        # Mantivemos a sua chamada original para fechar o navegador
        navegador.fechar_navegador()

# A parte abaixo foi atualizada para testes manuais, se necessário
if __name__ == "__main__":
    print("Este script agora é projetado para ser chamado pelo server.py.")
    print("Para testar, execute o trecho de código abaixo:")
    # print("Executando o RPA em modo de teste...")
    # processos_para_teste = database.buscar_processos_em_monitoramento_geral()
    # if processos_para_teste:
    #     executar_rpa(processos_para_teste)
    # else:
    #     print("Nenhum processo em monitoramento para testar.")