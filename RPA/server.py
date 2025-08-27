import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)

import main
from bd import database

database.inicializar_banco()

app = Flask(__name__)
CORS(app)

@app.route('/add-and-run', methods=['POST'])
def add_and_run_endpoint():
    """
    Recebe processos com responsáveis, adiciona/atualiza no banco
    e roda o RPA para eles.
    """
    try:
        data = request.get_json()
        processos_com_responsavel = data['processos']
        print(f"API: Adicionando e rodando para: {processos_com_responsavel}")

        # Salva os responsáveis no banco
        database.adicionar_processos_para_monitorar(processos_com_responsavel)
        
        # Extrai APENAS os números de processo para entregar ao robô
        numeros_processo = [item['numero'] for item in processos_com_responsavel]
        main.executar_rpa(numeros_processo)

        dados_painel = database.buscar_painel_dados()
        return jsonify(dados_painel)
    except Exception as e:
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/run-monitoring', methods=['POST'])
def run_monitoring_endpoint():
    """
    Busca todos os processos 'Em Monitoramento' no banco e roda o RPA para eles.
    """
    try:
        print("API: Iniciando RPA para processos em monitoramento...")
        processos_para_rodar = database.buscar_processos_em_monitoramento()
        
        if not processos_para_rodar:
            print("API: Nenhum processo encontrado para monitorar.")
            dados_painel = database.buscar_painel_dados()
            return jsonify(dados_painel)

        main.executar_rpa(processos_para_rodar)

        dados_painel = database.buscar_painel_dados()
        return jsonify(dados_painel)
    except Exception as e:
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/arquivar-processo', methods=['POST'])
def arquivar_processo_endpoint():
    """
    Recebe um número de processo e o move para o histórico (Arquivado).
    """
    try:
        data = request.get_json()
        numero_processo = data['numero_processo']
        database.marcar_como_arquivado(numero_processo)
        return jsonify({"success": True})
    except Exception as e:
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