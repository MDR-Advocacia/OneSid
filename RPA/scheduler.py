import schedule
import time
import sys
import os
from datetime import datetime
import threading  # <--- IMPORTANTE: Importamos o threading

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
#           (Esta função não muda, apenas seu agendamento)
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
#           (Esta função não muda)
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
#           NOVO: FUNÇÃO DE LOOP PARA A THREAD DO RPA
# ==================================================================
def loop_monitoramento_rpa():
    """
    Esta função viverá em uma thread separada, executando o RPA em loop.
    """
    print("-> [THREAD RPA] Iniciando loop de monitoramento RPA.")
    while True:
        try:
            # 1. Executa a tarefa de monitoramento
            executar_tarefa_monitoramento()
        except Exception as e:
            # Captura qualquer erro que a função 'executar_tarefa_monitoramento' não capturou
            print(f"!!! [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Erro crítico no loop de monitoramento RPA: {e} !!!")
        
        # 2. Pausa de 10 minutos
        print(f"\n--- [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] TAREFA RPA: Execução concluída. Aguardando 10 minutos antes da próxima... ---")
        time.sleep(60 * 10) # 60 segundos * 10 minutos

# ==================================================================
#           REGISTRO DE TAREFAS
# ==================================================================
# Tarefa 1: Rodar a cada 30 minutos (entre 8h e 20h)
# (A biblioteca 'schedule' rodará na Thread Principal)
schedule.every(30).minutes.do(tarefa_automatizada_completa)

# Tarefa 2 (RPA) não usa mais o 'schedule'. Ela será iniciada
# em sua própria thread no bloco main.
# ==================================================================


if __name__ == "__main__":
    print("✅✅ AGENDADOR UNIFICADO (COM THREADS) INICIADO ✅✅")
    print(f"-> Tarefa 1 (API Legal One) rodará a cada 30 MINUTOS (entre 8h e 20h).")
    print(f"-> Tarefa 2 (Monitoramento RPA) rodará em loop contínuo (executa, espera 10 MINUTOS, executa de novo).")
    print("Pressione Ctrl+C para encerrar.")
    
    # 1. Criar a thread para o loop do RPA
    # daemon=True garante que a thread feche se o script principal for encerrado
    thread_rpa = threading.Thread(target=loop_monitoramento_rpa, daemon=True)
    
    # 2. Iniciar a thread do RPA
    # Ela começará a rodar imediatamente em segundo plano
    thread_rpa.start()
    
    # 3. Executa a TAREFA API uma vez logo ao iniciar para teste
    print("\n[INICIALIZAÇÃO] Executando Tarefa API (1) pela primeira vez...")
    tarefa_automatizada_completa()
    print("\n[INICIALIZAÇÃO] Primeira execução concluída. Entrando no loop de agendamento...")

    # 4. O loop principal (Main Thread) agora só se preocupa
    #    em verificar o agendamento da TAREFA 1 (API).
    while True:
        schedule.run_pending()
        time.sleep(60) # Verifica a cada minuto se é hora de rodar a TAREFA 1