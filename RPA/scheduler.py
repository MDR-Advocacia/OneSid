import schedule
import time
import sys
import os
from datetime import datetime

# --- Adiciona o caminho do projeto para encontrar os módulos (só precisa fazer isso UMA VEZ) ---
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)
# --------------------------------------------------------------------------------------

# --- Importações de AMBOS os scripts ---
from bd import database
from RPA import apexFluxoLegalOne
from RPA import api_client
from RPA import main as rpa_main

# ==================================================================
#           TAREFA 1: IMPORTAÇÃO E POSTAGEM NA API
#           (Veio do seu 'scheduler_api.py')
# ==================================================================
def tarefa_automatizada_completa():
    """
    Orquestra a execução da importação, exportação e postagem para a API.
    """
    # Checagem de horário para não rodar entre 20h e 8h
    hora_atual = datetime.now().hour
    if not (8 <= hora_atual < 20):
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] TAREFA API: Fora do horário (8h-20h). Pulando.")
        return

    print(f"\n--- [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] INICIANDO TAREFA API (Legal One + Post) ---")

    # 1. Botão de Importar do Legal One
    print("[PASSO 1/3] Executando importação do Legal One...")
    try:
        resultados_importacao = apexFluxoLegalOne.main()
        print(f"Importação do Legal One concluída. {len(resultados_importacao)} tarefas processadas.")
    except Exception as e:
        print(f"!!! Erro na importação do Legal One: {e} !!!")


    # 2. Botão de Exportar JSON
    print("\n[PASSO 2/3] Executando exportação para JSON...")
    try:
        dados_exportados = database.exportar_dados_json()
        if not dados_exportados:
            print("Nenhum dado novo para exportar e postar.")
            print("--- TAREFA API CONCLUÍDA (sem postagem) ---")
            return
        print(f"Exportação JSON concluída. {len(dados_exportados)} processos para postar.")
        
        # Monta o objeto final no formato que a sua API de destino espera
        json_para_postar = {
            "fonte": "Onesid",
            "processos": dados_exportados
        }

    except Exception as e:
        print(f"!!! Erro na exportação para JSON: {e} !!!")
        return # Para a execução se a exportação falhar

    # 3. Postar o conteúdo na API
    print("\n[PASSO 3/3] Postando conteúdo para a API externa...")
    try:
        api_client.post_to_api(json_para_postar)
    except Exception as e:
        print(f"!!! Erro ao postar para a API externa: {e} !!!")

    print("\n--- TAREFA API FINALIZADA ---")


# ==================================================================
#           TAREFA 2: MONITORAMENTO RPA
#           (Veio do seu 'scheduler.py')
# ==================================================================
def executar_tarefa_monitoramento():
    """
    Esta é a função que o agendador irá chamar.
    Ela busca os processos que precisam ser monitorados e executa o robô para eles.
    """
    print(f"\n--- [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] INICIANDO TAREFA MONITORAMENTO (RPA) ---")
    print("Buscando processos que necessitam de monitoramento...")

    processos_para_rodar = database.buscar_processos_em_monitoramento_geral()

    if not processos_para_rodar:
        print("Nenhum processo na fila de monitoramento no momento.")
        return

    print(f"Encontrados {len(processos_para_rodar)} processo(s). Iniciando o RPA...")
    try:
        # Chama a função principal do robô com a lista de processos
        rpa_main.executar_rpa(processos_para_rodar)
        print("--- Tarefa de monitoramento agendada concluída com sucesso! ---")
    except Exception as e:
        print(f"!!! Ocorreu um erro durante a execução agendada do RPA: {e} !!!")


# ==================================================================
#           REGISTRO DE AMBAS AS TAREFAS
# ==================================================================
# Tarefa 1: Rodar a cada 2 horas (entre 8h e 20h)
schedule.every(2).hours.do(tarefa_automatizada_completa)

# Tarefa 2: Rodar a cada 50 minutos
schedule.every(50).minutes.do(executar_tarefa_monitoramento)
# ==================================================================


if __name__ == "__main__":
    print("✅✅ AGENDADOR UNIFICADO INICIADO ✅✅")
    print("-> Tarefa 1 (API Legal One) rodará a cada 2 horas (entre 8h e 20h).")
    print("-> Tarefa 2 (Monitoramento RPA) rodará a cada 50 minutos.")
    print("Pressione Ctrl+C para encerrar.")
    
    # Executa ambas as tarefas uma vez logo ao iniciar para teste
    print("\n[INICIALIZAÇÃO] Executando ambas as tarefas pela primeira vez...")
    executar_tarefa_monitoramento()
    tarefa_automatizada_completa()
    print("\n[INICIALIZAÇÃO] Primeira execução concluída. Entrando no loop de agendamento...")

    while True:
        # Verifica se há alguma tarefa agendada para ser executada
        schedule.run_pending()
        # Espera 60 segundos antes de verificar novamente
        time.sleep(60)