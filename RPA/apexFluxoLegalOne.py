# Substitua todo o conteúdo de RPA/apexFluxoLegalOne.py por este código:

import requests
import os
import json
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import bd.database as database

load_dotenv()

CLIENT_ID = os.environ.get("LEGAL_ONE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("LEGAL_ONE_CLIENT_SECRET")
BASE_URL = os.environ.get("LEGAL_ONE_BASE_URL")

auth_token_cache = { "token": None, "expires_at": datetime.now(UTC) }

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
        raise

def make_api_request(url, params):
    token = get_access_token()
    headers = { "Authorization": f"Bearer {token}" }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_all_tasks_candidates():
    print("Iniciando busca de tarefas candidatas...")
    all_tasks = []
    tipos_de_tarefa = [
        "(typeId eq 26 and subTypeId eq 1131)",
        "(typeId eq 18 and subTypeId eq 961)",
        "(typeId eq 18 and subTypeId eq 936)",
        "(typeId eq 18 and subTypeId eq 984)"
    ]

    for tipo in tipos_de_tarefa:
        print(f"\nBuscando os últimos 30 para o filtro: {tipo}")
        params = {
            "$filter": f"{tipo} and statusId eq 1 and relationships/any(r: r/linkType eq 'Litigation')",
            "$expand": "relationships($select=id,linkId)",
            "$select": "id,finishedBy,relationships",
            "$top": 30,
            "$orderby": "id desc"
        }
        url = f"{BASE_URL}/tasks"
        try:
            data = make_api_request(url, params=params)
            tasks_nesta_busca = data.get("value", [])
            all_tasks.extend(tasks_nesta_busca)
            print(f"-> Encontradas {len(tasks_nesta_busca)} candidatas.")
        except requests.exceptions.HTTPError as e:
            print(f"-> Erro ao buscar tarefas para este filtro: {e.response.text}")
            continue
    print(f"\nTotal de {len(all_tasks)} tarefas candidatas encontradas em todas as buscas.")
    return all_tasks

def get_litigation_by_id(litigation_id):
    url = f"{BASE_URL}/litigations/{litigation_id}?$select=identifierNumber"
    try:
        return make_api_request(url, params={})
    except requests.exceptions.HTTPError as e:
        return None

# --- FUNÇÃO PRINCIPAL MODIFICADA ---
def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        return []

    # 1. Busca a lista de candidatos
    tasks_candidatas = get_all_tasks_candidates()
    if not tasks_candidatas:
        print("Nenhuma tarefa candidata encontrada. Encerrando.")
        return []

    # 2. Filtra a lista para obter apenas as tarefas novas
    tasks_para_processar = database.filtrar_tarefas_novas(tasks_candidatas)
    
    if not tasks_para_processar:
        print("Nenhuma tarefa NOVA para processar. Encerrando.")
        return []

    # 3. Processa apenas a lista de tarefas novas
    final_results = []
    for task in tasks_para_processar:
        task_id = task.get('id')
        print(f"\nProcessando Tarefa NOVA ID: {task_id}...")
        user_id = task.get('finishedBy')
        litigation_id = task['relationships'][0].get('linkId') if task.get('relationships') else None
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