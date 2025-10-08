# apexFluxoLegalOne.py

import requests
import os
import json
import time
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv

# 1. Carrega o arquivo .env
load_dotenv()

# 2. DEFINE AS VARIÁVEIS (ESTE BLOCO É ESSENCIAL)
# ✅ Garanta que este bloco de código esteja aqui!
CLIENT_ID = os.environ.get("LEGAL_ONE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("LEGAL_ONE_CLIENT_SECRET")
BASE_URL = os.environ.get("LEGAL_ONE_BASE_URL")

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
auth_token_cache = {
    "token": None,
    "expires_at": datetime.now(UTC) # Linha já corrigida
}

# Cole esta versão corrigida no lugar da sua função get_access_token

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
        # AQUI ESTÁ A CORREÇÃO -> usando int() para converter o valor
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
    print("Buscando tarefas com typeId=26 e subTypeId=1131...")
    all_tasks = []
    
    # Parâmetros da nossa busca, agora com os filtros específicos
    params = {
        "$filter": "typeId eq 26 and subTypeId eq 1131 and relationships/any(r: r/linkType eq 'Litigation')",
        "$expand": "relationships"
    }
    
    # Monta a URL com os parâmetros
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    next_link = f"{BASE_URL}/tasks?{query_string}"

    page_num = 1
    while next_link:
        try:
            print(f"Buscando página {page_num} de tarefas...")
            data = make_api_request(next_link)
            tasks_on_page = data.get("value", [])
            all_tasks.extend(tasks_on_page)
            
            # A API informa o link para a próxima página em '@odata.nextLink'
            next_link = data.get("@odata.nextLink")
            page_num += 1
        except requests.exceptions.HTTPError as e:
            print(f"Erro ao buscar página de tarefas: {e.response.text}")
            break # Interrompe se houver erro em uma página

    print(f"Total de {len(all_tasks)} tarefas encontradas.")
    return all_tasks

def get_litigation_by_id(litigation_id):
    """
    Busca um processo específico pelo ID (forma otimizada).
    """
    url = f"{BASE_URL}/litigations/{litigation_id}"
    try:
        return make_api_request(url)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"AVISO: Processo com ID {litigation_id} não encontrado.")
        else:
            print(f"ERRO ao buscar processo {litigation_id}: {e.response.text}")
        return None # Retorna None se não encontrar ou der erro

def get_user_by_id(user_id):
    """
    Busca um usuário específico pelo ID (forma otimizada).
    """
    url = f"{BASE_URL}/Users/{user_id}"
    try:
        return make_api_request(url)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"AVISO: Usuário com ID {user_id} não encontrado.")
        else:
            print(f"ERRO ao buscar usuário {user_id}: {e.response.text}")
        return None # Retorna None se não encontrar ou der erro


# --- 3. EXECUÇÃO PRINCIPAL DO FLUXO ---
def main():
    """
    Função principal que orquestra todo o fluxo.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Erro: As variáveis de ambiente LEGAL_ONE_CLIENT_ID e LEGAL_ONE_CLIENT_SECRET não foram configuradas.")
        return

    tasks = get_all_tasks()
    if not tasks:
        print("Nenhuma tarefa para processar. Encerrando.")
        return

    final_results = []
    user_cache = {} # Cache para não buscar o mesmo usuário várias vezes

    for task in tasks:
        task_id = task.get('id')
        print(f"\nProcessando Tarefa ID: {task_id}...")

        # Extrai o ID do usuário que finalizou
        user_id = task.get('finishedBy')
        
        # Encontra o relacionamento com o processo (Litigation)
        litigation_id = None
        for rel in task.get('relationships', []):
            if rel.get('linkType') == 'Litigation':
                litigation_id = rel.get('linkId')
                break
        
        cnj_number = None
        user_name = None
        
        # Busca os dados do processo
        if litigation_id:
            litigation_data = get_litigation_by_id(litigation_id)
            if litigation_data:
                cnj_number = litigation_data.get('identifierNumber')
        
        # Busca os dados do usuário (usando cache)
        if user_id:
            if user_id in user_cache:
                user_name = user_cache[user_id]
                print(f"  -> Usuário {user_id} encontrado no cache: {user_name}")
            else:
                user_data = get_user_by_id(user_id)
                if user_data:
                    user_name = user_data.get('name')
                    user_cache[user_id] = user_name # Salva no cache
        
        # Monta o objeto final
        final_results.append({
            "tarefa_id": task_id,
            "tarefa_assunto": task.get('subject'),
            "data_conclusao": task.get('finishedOn'),
            "processo_id": litigation_id,
            "processo_cnj": cnj_number,
            "finalizado_por_id": user_id,
            "finalizado_por_nome": user_name
        })

    # Imprime e salva o resultado final
    print("\n--- RESULTADO FINAL ---")
    
    # Salva os resultados em um arquivo JSON
    nome_do_arquivo = "resultado_tarefas.json"
    with open(nome_do_arquivo, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    print(f"Resultados salvos com sucesso no arquivo: {nome_do_arquivo}")

    return final_results

if __name__ == "__main__":
    main()