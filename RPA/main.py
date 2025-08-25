from playwright.sync_api import sync_playwright
import config
import navegador
import portal_bb
import processo
from bd import database # Importamos o database para usar a função de atualização

def executar_rpa(lista_processos: list):
    """
    Orquestra a execução do robô para uma lista de processos,
    atualizando o banco de dados com os resultados de cada um.
    """
    try:
        with sync_playwright() as p:
            browser = navegador.iniciar_e_conectar(p)
            context = browser.contexts[0]
            
            portal_page = portal_bb.fazer_login(context, config.EXTENSION_URL)
            
            for num_processo in lista_processos:
                print(f"\n--- INICIANDO CONSULTA PARA O PROCESSO: {num_processo} ---")
                try:
                    processo.navegar_para_processo(portal_page, num_processo, config.URL_BUSCA_PROCESSO)
                    processo.acessar_detalhes(portal_page, num_processo)
                    processo.clicar_menu_subsidios(portal_page, num_processo)
                    
                    # Extrai os dados dos subsídios para o processo atual
                    dados_subsidios_do_processo = processo.extrair_dados_subsidios(portal_page)
                    
                    # Se encontrou dados, atualiza o status no banco de dados
                    if dados_subsidios_do_processo:
                        database.atualizar_status_processo(num_processo, dados_subsidios_do_processo)
                    else:
                        print(f"AVISO: Nenhum subsídio encontrado para o processo {num_processo}. Status não atualizado.")

                except Exception as e:
                    print(f"!!!!!!!!!!!!!! ERRO AO PROCESSAR O PROCESSO {num_processo} !!!!!!!!!!!!!!")
                    print(f"Detalhes do erro: {e}")
                    print("Continuando para o próximo processo...")
                    continue # Pula para o próximo item da lista em caso de erro

            print("\n✅ CONSULTA RPA FINALIZADA PARA TODOS OS PROCESSOS SOLICITADOS.")

    except Exception as e:
        print("\n========================= ERRO GERAL NO RPA =========================")
        print(f"Ocorreu uma falha crítica na automação: {e}")
        print("=====================================================================")
    finally:
        navegador.fechar_navegador()

# A parte abaixo pode ser usada para testes manuais, se necessário
if __name__ == "__main__":
    # Para testar, você pode chamar as funções do banco e do rpa diretamente aqui
    # Ex: database.inicializar_banco()
    # Ex: executar_rpa(["0032782-96.2023.8.03.0001"])
    print("Este script agora é projetado para ser chamado pelo server.py.")