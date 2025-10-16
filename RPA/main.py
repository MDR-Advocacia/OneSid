import sys
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from playwright.sync_api import sync_playwright
from RPA import navegador, portal_bb, processo, config
from bd import database

# --- CONFIGURAÇÃO DO LOG ---

# Configuração do caminho para importação e logs
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)

# Cria o diretório de logs se não existir
log_dir = os.path.join(caminho_raiz_do_projeto, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'rpa_execution.log')

# Configura o logger para salvar em arquivo e mostrar no console
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Evita a duplicação de handlers se o script for importado várias vezes
if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Handler para salvar em arquivo com rotação (5MB por arquivo, até 2 backups)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para exibir no console
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def executar_rpa(lista_processos: list, funcao_de_atualizacao=database.atualizar_status_para_usuarios):
    """
    Executa o robô de RPA com uma lógica de 2 tentativas e logging detalhado.
    """
    logging.info("--- INICIANDO EXECUÇÃO DO RPA ---")
    browser = None
    processos_para_tentar = lista_processos[:] # Cria uma cópia para não modificar a original

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

            # Loop principal de tentativas (até 2 vezes)
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
                        logging.info(f"  a. Navegando para a página do processo...")
                        processo.navegar_para_processo(portal_page, num_processo, config.URL_BUSCA_PROCESSO)
                        
                        logging.info(f"  b. Acessando detalhes e subsídios...")
                        processo.acessar_detalhes(portal_page, num_processo)
                        processo.clicar_menu_subsidios(portal_page, num_processo)
                        
                        logging.info(f"  c. Extraindo dados da tabela...")
                        dados_subsidios_do_processo = processo.extrair_dados_subsidios(portal_page)
                        
                        if dados_subsidios_do_processo:
                            logging.info(f"  d. Encontrados {len(dados_subsidios_do_processo)} subsídios. Atualizando banco de dados...")
                            funcao_de_atualizacao(num_processo, dados_subsidios_do_processo)
                            logging.info(f"  ✔️ SUCESSO: Banco de dados atualizado para o processo {num_processo}.")
                        else:
                            logging.info(f"  d. Nenhum subsídio encontrado para {num_processo}.")
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
                    logging.critical(f"  - {num_proc}")

            logging.info("✅ CONSULTA RPA FINALIZADA.")

    except Exception:
        logging.critical("========================= ERRO GERAL NO RPA =========================", exc_info=True)
    finally:
        if browser:
            logging.info("3. Fechando navegador...")
            navegador.fechar_navegador()
        logging.info("--- EXECUÇÃO DO RPA FINALIZADA ---")

if __name__ == "__main__":
    logging.info("Este script é projetado para ser chamado pelo server.py ou scheduler.py.")

