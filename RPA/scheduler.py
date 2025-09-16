import schedule
import time
import sys
import os
from datetime import datetime

# --- Adiciona o caminho do projeto para encontrar os módulos ---
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)
# -----------------------------------------------------------

from bd import database
from RPA import main as rpa_main

def executar_tarefa_monitoramento():
    """
    Esta é a função que o agendador irá chamar.
    Ela busca os processos que precisam ser monitorados e executa o robô para eles.
    """
    print(f"\n--- [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Agendador ativado! ---")
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
#               CONFIGURE O AGENDAMENTO AQUI
# ==================================================================
# Deixei ativo apenas o agendamento para cada 10 minutos, como solicitado.

# Exemplo 1: Rodar a cada 4 horas.
# schedule.every(4).hours.do(executar_tarefa_monitoramento)

# Exemplo 2: Rodar uma vez por dia às 09:00 da manhã.
# schedule.every().day.at("09:00").do(executar_tarefa_monitoramento)

# ATIVO PARA TESTES: Rodar a cada 50 minutos.
schedule.every(50).minutes.do(executar_tarefa_monitoramento)
# ==================================================================


if __name__ == "__main__":
    print("✅ Agendador de Monitoramento Automático Iniciado.")
    print("O robô será executado a cada 50 minutos.")
    print("Pressione Ctrl+C para encerrar.")
    
    # Executa a tarefa uma vez logo ao iniciar o script
    executar_tarefa_monitoramento() 

    while True:
        # Verifica se há alguma tarefa agendada para ser executada
        schedule.run_pending()
        # Espera 1 minuto antes de verificar novamente
        time.sleep(60)