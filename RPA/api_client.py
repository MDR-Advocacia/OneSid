# RPA/api_client.py
import requests
import json
from RPA import config

def post_to_api(data, url=config.API_TASKS_BATCH_URL):
    """
    Posts the given data as JSON to the specified URL.
    """
    headers = {'Content-Type': 'application/json'}
    try:
        # Usamos json.dumps para converter o dicionário em uma string JSON
        response = requests.post(url, data=json.dumps(data), headers=headers)
        response.raise_for_status()  # Lança uma exceção para respostas de erro (4xx ou 5xx)
        print(f"Dados postados com sucesso para a API: {url}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao postar dados para a API: {e}")
        return None