import sys
import os
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openpyxl import Workbook
from io import BytesIO

# --- CORREÇÃO DO CAMINHO DE IMPORTAÇÃO ---
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)
# -----------------------------------------

import main
from bd import database

database.inicializar_banco()

app = Flask(__name__)
CORS(app)

@app.route('/itens-relevantes', methods=['GET'])
def get_itens_relevantes():
    try:
        itens = database.buscar_itens_relevantes()
        return jsonify(itens)
    except Exception as e:
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/itens-relevantes', methods=['POST'])
def post_itens_relevantes():
    try:
        data = request.get_json()
        itens = data['itens']
        database.salvar_itens_relevantes(itens)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/add-and-run', methods=['POST'])
def add_and_run_endpoint():
    """
    Recebe processos com responsáveis e classificação, adiciona/atualiza no banco
    e roda o RPA para eles.
    """
    try:
        data = request.get_json()
        processos_com_dados = data['processos']
        print(f"API: Adicionando e rodando para: {processos_com_dados}")

        # Salva os dados completos no banco
        database.adicionar_processos_para_monitorar(processos_com_dados)
        
        # Extrai apenas os números de processo para entregar ao robô
        numeros_processo = [item['numero'] for item in processos_com_dados]
        main.executar_rpa(numeros_processo)

        dados_painel = database.buscar_painel_dados()
        return jsonify(dados_painel)
    except Exception as e:
        traceback.print_exc()
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
        traceback.print_exc()
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

@app.route('/export-excel', methods=['GET'])
def export_excel_endpoint():
    """
    Busca os dados do painel e do histórico e gera um arquivo Excel para download.
    """
    try:
        # 1. Busca os dados do banco
        dados_painel = database.buscar_painel_dados()
        dados_historico = database.buscar_historico_arquivado()

        # 2. Cria a planilha em memória
        workbook = Workbook()
        
        # --- Planilha 1: Painel de Controle ---
        sheet_painel = workbook.active
        sheet_painel.title = "Painel de Controle"

        # Cabeçalhos
        headers_painel = ["ID", "Responsável", "Processo", "Classificação", "Status", "Última Verificação"]
        sheet_painel.append(headers_painel)

        # Dados
        for processo in dados_painel:
            sheet_painel.append([
                processo['id'],
                processo['responsavel_principal'],
                processo['numero_processo'],
                processo['classificacao'],
                processo['status_geral'],
                processo['data_ultima_atualizacao']
            ])

        # --- Planilha 2: Histórico ---
        if dados_historico:
            sheet_historico = workbook.create_sheet(title="Histórico")
            headers_historico = ["ID", "Responsável", "Processo", "Classificação", "Data de Arquivamento"]
            sheet_historico.append(headers_historico)
            for processo in dados_historico:
                sheet_historico.append([
                    processo['id'],
                    processo['responsavel_principal'],
                    processo['numero_processo'],
                    processo['classificacao'],
                    processo['data_ultima_atualizacao']
                ])

        # 3. Salva o arquivo em um buffer de memória
        excel_buffer = BytesIO()
        workbook.save(excel_buffer)
        excel_buffer.seek(0) # Volta para o início do buffer para a leitura

        # 4. Envia o arquivo para o front-end
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name='onesid_export.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro ao gerar a planilha: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)