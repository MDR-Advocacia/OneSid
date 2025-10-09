# Substitua todo o conteúdo de RPA/apexFluxoLegalOne.py por este código:

import requests
import os
import json
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv

# 1. Carrega o arquivo .env
load_dotenv()

# 2. DEFINE AS VARIÁVEIS
CLIENT_ID = os.environ.get("LEGAL_ONE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("LEGAL_ONE_CLIENT_SECRET")
BASE_URL = os.environ.get("LEGAL_ONE_BASE_URL")

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
auth_token_cache = {
    "token": None,
    "expires_at": datetime.now(UTC)
}

def get_access_token():
    if auth_token_cache["token"] and datetime.now(UTC) < auth_token_cache["expires_at"] - timedelta(seconds=60):
        return auth_token_cache["token"]

    print("Gerando um novo token de acesso...")
    auth_url = "https://api.thomsonreuters.com/legalone/oauth?grant_type=client_credentials"
    
    try:
        response = requests.post(auth_url, auth=(CLIENT_ID, CLIENT_SECRET))
        response.raise_for_status()
        data = response.json()
        
        auth_token_cache["token"] = data["access_token"]
        expires_in = int(data.get("expires_in", 1800))
        auth_token_cache["expires_at"] = datetime.now(UTC) + timedelta(seconds=expires_in)
        
        print("Token gerado com sucesso!")
        return auth_token_cache["token"]
    except requests.exceptions.HTTPError as e:
        print(f"Erro CRÍTICO ao obter token: {e.response.status_code} - {e.response.text}")
        raise

def make_api_request(url, params):
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# --- 2. FUNÇÕES PARA BUSCAR OS DADOS ---

# --- FUNÇÃO TOTALMENTE REESCRITA ---
def get_all_tasks():
    """
    Busca os últimos 30 registros de cada tipo de tarefa especificada, 
    filtrando apenas aquelas com status 'cumprido' (statusId: 1).
    """
    print("Iniciando busca limitada de tarefas...")
    
    all_tasks = []
    
    # Lista dos diferentes tipos de tarefas que queremos buscar
    tipos_de_tarefa = [
        "(typeId eq 26 and subTypeId eq 1131)",
        "(typeId eq 18 and subTypeId eq 961)",
        "(typeId eq 18 and subTypeId eq 936)",
        "(typeId eq 18 and subTypeId eq 984)"
    ]

    # Loop para fazer uma requisição para cada tipo de tarefa
    for tipo in tipos_de_tarefa:
        print(f"\nBuscando os últimos 30 registros para o filtro: {tipo}")
        
        # Parâmetros para esta busca específica
        params = {
            "$filter": f"{tipo} and statusId eq 1 and relationships/any(r: r/linkType eq 'Litigation')",
            "$expand": "relationships($select=id,linkId)",
            "$select": "id,finishedBy,relationships",
            "$top": 30,          # Limita aos 30 primeiros resultados
            "$orderby": "id desc" # Ordena do mais recente para o mais antigo
        }
        
        url = f"{BASE_URL}/tasks"
        
        try:
            data = make_api_request(url, params=params)
            tasks_nesta_busca = data.get("value", [])
            all_tasks.extend(tasks_nesta_busca)
            print(f"-> Encontradas {len(tasks_nesta_busca)} tarefas.")
        except requests.exceptions.HTTPError as e:
            print(f"-> Erro ao buscar tarefas para este filtro: {e.response.text}")
            # Continua para o próximo tipo de tarefa mesmo se um falhar
            continue

    print(f"\nTotal de {len(all_tasks)} tarefas encontradas em todas as buscas.")
    return all_tasks

def get_litigation_by_id(litigation_id):
    url = f"{BASE_URL}/litigations/{litigation_id}?$select=identifierNumber"
    try:
        # Passando um dicionário vazio de parâmetros
        return make_api_request(url, params={})
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"AVISO: Processo com ID {litigation_id} não encontrado.")
        else:
            print(f"ERRO ao buscar processo {litigation_id}: {e.response.text}")
        return None

# --- 3. EXECUÇÃO PRINCIPAL DO FLUXO (VERSÃO ENXUTA) ---
def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Erro: As variáveis de ambiente não foram configuradas.")
        return []

    tasks = get_all_tasks()
    if not tasks:
        print("Nenhuma tarefa para processar. Encerrando.")
        return []

    final_results = []

    for task in tasks:
        task_id = task.get('id')
        print(f"\nProcessando Tarefa ID: {task_id}...")

        user_id = task.get('finishedBy')
        
        litigation_id = None
        if task.get('relationships'):
            litigation_id = task['relationships'][0].get('linkId')
        
        cnj_number = None
        if litigation_id:
            litigation_data = get_litigation_by_id(litigation_id)
            if litigation_data:
                cnj_number = litigation_data.get('identifierNumber')
        
        final_results.append({
            "tarefa_id": task_id,
            "processo_id": litigation_id,
            "processo_cnj": cnj_number,
            "finalizado_por_id": user_id,
        })

    print("\n--- RESULTADO FINAL ---")
    
    nome_do_arquivo = "resultado_tarefas.json"
    with open(nome_do_arquivo, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    print(f"Resultados salvos com sucesso no arquivo: {nome_do_arquivo}")
    return final_results

if __name__ == "__main__":
    main()