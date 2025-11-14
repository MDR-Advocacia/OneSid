import sys
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from playwright.sync_api import sync_playwright

# --- CONFIGURAÇÃO DO CAMINHO E IMPORTS (AJUSTADOS) ---
# Garante que o 'bd' seja encontrado mesmo quando importado
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
if caminho_raiz_do_projeto not in sys.path:
    sys.path.append(caminho_raiz_do_projeto)

from RPA import navegador, portal_bb, processo, config
from bd import database

# --- CONFIGURAÇÃO DO LOG ---
# (O seu código de logging está ótimo e será mantido)
log_dir = os.path.join(caminho_raiz_do_projeto, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'rpa_execution.log')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def executar_rpa(lista_processos: list, funcao_de_atualizacao=database.atualizar_status_para_usuarios):
    """
    Executa o robô de RPA com uma lógica de 2 tentativas e logging detalhado.
    (Esta é a sua função original, mantida 100% intacta)
    """
    logging.info("--- INICIANDO EXECUÇÃO DO RPA ---")
    browser = None
    processos_para_tentar = lista_processos[:] 

    try:
        with sync_playwright() as p:
            browser = navegador.iniciar_e_conectar(p)
            if not browser:
                logging.error("Falha ao iniciar o navegador. Abortando.")
                return

            context = browser.contexts[0]
            
            logging.info("1. Realizando login no portal...")
            portal_page = portal_bb.fazer_login(context, config.EXTENSION_URL)
            if not portal_page:
                logging.error("Falha no login. Verifique as credenciais ou a página.")
                return
            logging.info("✔️ Login realizado com sucesso.")

            for tentativa in range(1, 3):
                if not processos_para_tentar:
                    logging.info("Todos os processos foram concluídos com sucesso.")
                    break

                logging.info(f"{'='*20} TENTATIVA {tentativa} de 2 {'='*20}")
                logging.info(f"Processando {len(processos_para_tentar)} processo(s).")
                
                processos_falhados_nesta_tentativa = []

                for num_processo in processos_para_tentar:
                    try:
                        portal_page = portal_bb.verificar_e_renovar_sessao(portal_page, context, config.EXTENSION_URL)

                        logging.info(f"--- Processando: {num_processo} ---")
                        logging.info(f" 	a. Navegando para a página do processo...")
                        processo.navegar_para_processo(portal_page, num_processo, config.URL_BUSCA_PROCESSO)
                        
                        logging.info(f" 	b. Acessando detalhes e subsídios...")
                        processo.acessar_detalhes(portal_page, num_processo)
                        processo.clicar_menu_subsidios(portal_page, num_processo)
                        
                        logging.info(f" 	c. Extraindo dados da tabela...")
                        dados_subsidios_do_processo = processo.extrair_dados_subsidios(portal_page)
                        
                        if dados_subsidios_do_processo:
                            logging.info(f" 	d. Encontrados {len(dados_subsidios_do_processo)} subsídios. Atualizando banco de dados...")
                            funcao_de_atualizacao(num_processo, dados_subsidios_do_processo)
                            logging.info(f" 	✔️ SUCESSO: Banco de dados atualizado para o processo {num_processo}.")
                        else:
                            logging.info(f" 	d. Nenhum subsídio encontrado para {num_processo}.")
                            funcao_de_atualizacao(num_processo, []) 

                    except Exception:
                        logging.error(f"ERRO AO PROCESSAR {num_processo} NA TENTATIVA {tentativa}", exc_info=True)
                        processos_falhados_nesta_tentativa.append(num_processo)
                        continue
                
                processos_para_tentar = processos_falhados_nesta_tentativa
                
                if processos_para_tentar:
                    logging.warning(f"--- Fim da Tentativa {tentativa}. {len(processos_para_tentar)} processos falharam e serão reprocessados. ---")
                    time.sleep(10)

            if processos_para_tentar:
                logging.critical("‼️ ATENÇÃO: Os seguintes processos falharam após 2 tentativas:")
                for num_proc in processos_para_tentar:
                    logging.critical(f" 	- {num_proc}")

            logging.info("✅ CONSULTA RPA FINALIZADA.")

    except Exception:
        logging.critical("========================= ERRO GERAL NO RPA =========================", exc_info=True)
    finally:
        if browser:
            logging.info("3. Fechando navegador...")
            navegador.fechar_navegador()
        logging.info("--- EXECUÇÃO DO RPA FINALIZADA ---")


# --- INÍCIO DAS MUDANÇAS ---

def main():
    """
    Função principal que o SCHEDULER.PY irá chamar.
    Ela busca os dados e chama o robô.
    """
    logging.info("Função main() do RPA iniciada. Buscando processos no banco...")
    try:
        # 1. Buscar a lista de processos do banco de dados
        # (Esta é a lista que o `executar_rpa` precisa)
        lista_processos_para_monitorar = database.buscar_processos_em_monitoramento_geral()

        if not lista_processos_para_monitorar:
            logging.info("Nenhum processo em 'monitorando' encontrado no banco. Ciclo de RPA pulado.")
            return # Não há o que fazer

        logging.info(f"Encontrados {len(lista_processos_para_monitorar)} processos para monitorar.")
        
        # 2. Chamar a função principal do robô com a lista
        # (Passando a lista que acabamos de buscar)
        executar_rpa(lista_processos_para_monitorar)

    except Exception as e:
        logging.critical(f"Erro catastrófico na função main() antes de iniciar o executar_rpa: {e}", exc_info=True)

if __name__ == "__main__":
    # Agora, se você executar "python RPA/main.py" diretamente,
    # ele vai rodar a lógica completa, o que é ótimo para testes.
    logging.info("Script main.py executado diretamente. Iniciando o processo...")
    main()