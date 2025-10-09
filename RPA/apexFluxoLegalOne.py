# apexFluxoLegalOne.py

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
    """
    Verifica se o token atual é válido e, se não for, gera um novo.
    """
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

def make_api_request(url):
    """
    Função auxiliar para fazer uma requisição GET já com o cabeçalho de autenticação.
    """
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# --- 2. FUNÇÕES PARA BUSCAR OS DADOS ---

def get_all_tasks():
    """
    Busca todas as tarefas vinculadas a processos, cuidando da paginação.
    """
    print("Buscando tarefas (versão robusta)...")
    all_tasks = []
    
    params = {
        "$filter": "typeId eq 26 and subTypeId eq 1131 and relationships/any(r: r/linkType eq 'Litigation')",
        "$expand": "relationships"
    }
    
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    next_link = f"{BASE_URL}/tasks?{query_string}"

    page_num = 1
    while next_link:
        try:
            print(f"Buscando página {page_num} de tarefas...")
            data = make_api_request(next_link)
            tasks_on_page = data.get("value", [])
            all_tasks.extend(tasks_on_page)
            
            next_link = data.get("@odata.nextLink")
            page_num += 1
        except requests.exceptions.HTTPError as e:
            print(f"Erro ao buscar página de tarefas: {e.response.text}")
            break

    print(f"Total de {len(all_tasks)} tarefas encontradas.")
    return all_tasks

def get_litigation_by_id(litigation_id):
    """
    Busca um processo pelo ID, mas retorna APENAS o campo 'identifierNumber'.
    """
    url = f"{BASE_URL}/litigations/{litigation_id}?$select=identifierNumber"
    try:
        return make_api_request(url)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"AVISO: Processo com ID {litigation_id} não encontrado.")
        else:
            print(f"ERRO ao buscar processo {litigation_id}: {e.response.text}")
        return None

# --- 3. EXECUÇÃO PRINCIPAL DO FLUXO ---
def main():
    """
    Função principal que orquestra todo o fluxo.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Erro: As variáveis de ambiente não foram configuradas.")
        return

    tasks = get_all_tasks()
    if not tasks:
        print("Nenhuma tarefa para processar. Encerrando.")
        return

    final_results = []

    for task in tasks:
        task_id = task.get('id')
        print(f"\nProcessando Tarefa ID: {task_id}...")

        user_id = task.get('finishedBy')
        
        litigation_id = None
        for rel in task.get('relationships', []):
            if rel.get('linkType') == 'Litigation':
                litigation_id = rel.get('linkId')
                break
        
        cnj_number = None
        
        if litigation_id:
            litigation_data = get_litigation_by_id(litigation_id)
            if litigation_data:
                cnj_number = litigation_data.get('identifierNumber')

        # ✅ Objeto final agora está mais limpo
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