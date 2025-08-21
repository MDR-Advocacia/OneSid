import json # Importa a biblioteca para trabalhar com JSON
from playwright.sync_api import sync_playwright
import config
import navegador
import portal_bb
import processo

def run():
    """
    Função principal que orquestra a execução do robô.
    """
    lista_processos = ["0829659-38.2024.8.23.0010"]
    todos_os_subsidios = []

    try:
        with sync_playwright() as p:
            browser = navegador.iniciar_e_conectar(p)
            context = browser.contexts[0]
            
            portal_page = portal_bb.fazer_login(context, config.EXTENSION_URL)
            
            for num_processo in lista_processos:
                processo.navegar_para_processo(portal_page, num_processo, config.URL_BUSCA_PROCESSO)
                
                processo.acessar_detalhes(portal_page, num_processo)
                
                processo.clicar_menu_subsidios(portal_page, num_processo)
                
                # --- NOVA ETAPA ADICIONADA AQUI ---
                dados_do_processo = processo.extrair_dados_subsidios(portal_page)
                
                # Adiciona os dados extraídos à lista geral
                if dados_do_processo:
                    todos_os_subsidios.append({
                        "processo": num_processo,
                        "subsidios": dados_do_processo
                    })
                # ------------------------------------
                
            print("\n✅ TODOS OS PROCESSOS FORAM CONSULTADOS E DADOS EXTRAÍDOS.")

    except Exception as e:
        print("\n========================= ERRO =========================")
        print(f"Ocorreu uma falha na automação: {e}")
        print("========================================================")
    finally:
        # --- SALVANDO OS DADOS EM ARQUIVO JSON ---
        if todos_os_subsidios:
            nome_arquivo = "subsidios.json"
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                json.dump(todos_os_subsidios, f, ensure_ascii=False, indent=4)
            print(f"\n💾 Dados salvos com sucesso no arquivo: {nome_arquivo}")
        # ------------------------------------------
            
        navegador.fechar_navegador()


if __name__ == "__main__":
    run()