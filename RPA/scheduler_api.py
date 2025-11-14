# RPA/scheduler.py
# RPA/scheduler.py
# RPA/scheduler.py
# RPA/scheduler.py

import schedule
import time
import sys
import os
from datetime import datetime

# Adiciona o caminho do projeto para encontrar os módulos
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)

# Importações dos módulos do projeto
from RPA import apexFluxoLegalOne
from bd import database
from RPA import api_client # Novo import

def tarefa_automatizada_completa():
    """
    Orquestra a execução da importação, exportação e postagem para a API.
    """
    # NOVO: Checagem de horário para não rodar entre 20h e 8h
    hora_atual = datetime.now().hour
    if not (8 <= hora_atual < 20):
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Fora do horário de execução (8h-20h). Pulando esta execução.")
        return

    print(f"\n--- [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] INICIANDO TAREFA AUTOMATIZIZADA COMPLETA ---")

    # 1. Botão de Importar do Legal One
    print("\n[PASSO 1/3] Executando importação do Legal One...")
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
            print("--- TAREFA AUTOMATIZADA CONCLUÍDA (sem postagem) ---")
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

    print("\n--- TAREFA AUTOMATIZADA COMPLETA FINALIZADA ---")


# ==================================================================
#               CONFIGURE O AGENDAMENTO AQUI
# ==================================================================
# Rodar a cada 2 horas, como solicitado.
#schedule.every(2).hours.do(tarefa_automatizada_completa)

# Novo agendamento (a cada 30 minutos):
schedule.every(30).minutes.do(tarefa_automatizada_completa)
# ==================================================================


if __name__ == "__main__":
    print("✅ Agendador de Tarefas Automáticas Iniciado.")
    print("A rotina completa será executada a cada 2 horas, somente entre 8h e 20h.")
    print("Pressione Ctrl+C para encerrar.")

    # Executa a tarefa uma vez logo ao iniciar o script para teste imediato
    tarefa_automatizada_completa()

    while True:
        schedule.run_pending()
        time.sleep(30)