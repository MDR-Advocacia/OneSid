import json
from playwright.sync_api import sync_playwright
import config
import navegador
import portal_bb
import processo

# A lógica principal agora é uma função que aceita uma lista de processos
def executar_rpa(lista_processos: list) -> list:
    """
    Função principal que orquestra a execução do robô.
    Recebe uma lista de números de processo e retorna os dados extraídos.
    """
    todos_os_subsidios = []

    try:
        with sync_playwright() as p:
            browser = navegador.iniciar_e_conectar(p)
            context = browser.contexts[0]
            
            portal_page = portal_bb.fazer_login(context, config.EXTENSION_URL)
            
            for num_processo in lista_processos:
                print(f"\n--- INICIANDO CONSULTA PARA O PROCESSO: {num_processo} ---")
                processo.navegar_para_processo(portal_page, num_processo, config.URL_BUSCA_PROCESSO)
                processo.acessar_detalhes(portal_page, num_processo)
                processo.clicar_menu_subsidios(portal_page, num_processo)
                
                dados_do_processo = processo.extrair_dados_subsidios(portal_page)
                
                if dados_do_processo:
                    todos_os_subsidios.append({
                        "processo": num_processo,
                        "subsidios": dados_do_processo
                    })
                
            print("\n✅ TODOS OS PROCESSOS FORAM CONSULTADOS E DADOS EXTRAÍDOS.")
            return todos_os_subsidios

    except Exception as e:
        print("\n========================= ERRO =========================")
        print(f"Ocorreu uma falha na automação: {e}")
        print("========================================================")
        # Em caso de erro, retorna a lista com o que foi coletado até o momento
        return todos_os_subsidios
    finally:
        # A parte de fechar o navegador será controlada pelo servidor agora
        navegador.fechar_navegador()

# A parte abaixo só será executada se você rodar `python main.py` diretamente
# Ótimo para testes!
if __name__ == "__main__":
    processos_para_teste = ["0803535-15.2025.8.20.5103"]
    resultado = executar_rpa(processos_para_teste)
    
    if resultado:
        nome_arquivo = "subsidios_teste.json"
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=4)
        print(f"\n💾 Dados de teste salvos com sucesso no arquivo: {nome_arquivo}")