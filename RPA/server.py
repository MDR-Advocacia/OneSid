import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CORREÇÃO DO CAMINHO DE IMPORTAÇÃO ---
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)
# -----------------------------------------

import main
from bd import database

# Garante que o banco de dados e suas tabelas existam ao iniciar
database.inicializar_banco()

app = Flask(__name__)
CORS(app)

@app.route('/submit-processos', methods=['POST'])
def submit_processos_endpoint():
    """
    Recebe novos processos do painel, adiciona ao monitoramento
    e dispara a execução do RPA apenas para os que precisam.
    """
    try:
        data = request.get_json()
        if not data or 'processos' not in data:
            return jsonify({"error": "A lista de 'processos' não foi encontrada."}), 400
            
        numeros_processo = data['processos']
        print(f"API recebeu submissão para os processos: {numeros_processo}")

        # 1. Adiciona os novos processos à tabela de monitoramento
        database.adicionar_processos_para_monitorar(numeros_processo)

        # 2. Executa o RPA para os processos submetidos
        # (Em uma versão futura, poderíamos rodar apenas os que estão 'Em Monitoramento')
        main.executar_rpa(numeros_processo)

        # 3. Retorna os dados atualizados do painel
        dados_painel = database.buscar_painel_dados()
        return jsonify(dados_painel)

    except Exception as e:
        print(f"Ocorreu um erro no endpoint /submit-processos: {e}")
        return jsonify({"error": f"Ocorreu um erro interno no servidor: {e}"}), 500

@app.route('/arquivar-processo', methods=['POST'])
def arquivar_processo_endpoint():
    """
    Recebe um número de processo e o move para o histórico (Arquivado).
    """
    try:
        data = request.get_json()
        numero_processo = data['numero_processo']
        database.marcar_como_arquivado(numero_processo)
        return jsonify({"success": True, "message": f"Processo {numero_processo} arquivado."})
    except Exception as e:
        print(f"Ocorreu um erro ao arquivar o processo: {e}")
        return jsonify({"error": f"Erro ao arquivar: {e}"}), 500

@app.route('/painel', methods=['GET'])
def get_painel_endpoint():
    """
    Retorna os dados dos processos que estão sendo monitorados ou pendentes.
    """
    dados_painel = database.buscar_painel_dados()
    return jsonify(dados_painel)

@app.route('/historico', methods=['GET'])
def get_historico_endpoint():
    """
    Retorna os dados dos processos que já foram arquivados.
    """
    historico = database.buscar_historico_arquivado()
    return jsonify(historico)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)