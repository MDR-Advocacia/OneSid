import sys
import os
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from openpyxl import Workbook
from io import BytesIO

# --- CORREÇÃO DO CAMINHO DE IMPORTAÇÃO (existente) ---
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)
# -----------------------------------------

import main
from bd import database

# Inicializa o banco de dados antes de tudo
database.inicializar_banco()

app = Flask(__name__)

# --- CONFIGURAÇÕES DA APLICAÇÃO ---
# Adiciona a chave secreta para o JWT
app.config["JWT_SECRET_KEY"] = "uma-chave-super-secreta-e-diferente" # Mude para uma chave segura

# Habilita o CORS para a aplicação
CORS(app, resources={r"/*": {"origins": "*"}}) 

# Inicializa o JWTManager com a aplicação
jwt = JWTManager(app)
# --- FIM DAS CONFIGURAÇÕES ---


# --- ROTA DE LOGIN ---
@app.route('/login', methods=['POST'])
def login_endpoint():
    data = request.get_json()
    username = data.get('username', None)
    password = data.get('password', None)

    user = database.buscar_usuario_por_nome(username)
    
    if user and check_password_hash(user['password_hash'], password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)
    
    return jsonify({"msg": "Usuário ou senha inválidos"}), 401
# --- FIM DA ROTA DE LOGIN ---


# --- ROTAS PROTEGIDAS ---

@app.route('/itens-relevantes', methods=['GET'])
@jwt_required()
def get_itens_relevantes():
    try:
        itens = database.buscar_itens_relevantes()
        return jsonify(itens)
    except Exception as e:
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/itens-relevantes', methods=['POST'])
@jwt_required()
def post_itens_relevantes():
    try:
        data = request.get_json()
        itens = data['itens']
        database.salvar_itens_relevantes(itens)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/add-and-run', methods=['POST'])
@jwt_required()
def add_and_run_endpoint():
    try:
        data = request.get_json()
        processos_com_dados = data['processos']
        database.adicionar_processos_para_monitorar(processos_com_dados)
        numeros_processo = [item['numero'] for item in processos_com_dados]
        main.executar_rpa(numeros_processo)
        dados_painel = database.buscar_painel_dados()
        return jsonify(dados_painel)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/run-monitoring', methods=['POST'])
@jwt_required()
def run_monitoring_endpoint():
    try:
        processos_para_rodar = database.buscar_processos_em_monitoramento()
        if not processos_para_rodar:
            dados_painel = database.buscar_painel_dados()
            return jsonify(dados_painel)
        main.executar_rpa(processos_para_rodar)
        dados_painel = database.buscar_painel_dados()
        return jsonify(dados_painel)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/arquivar-processo', methods=['POST'])
@jwt_required()
def arquivar_processo_endpoint():
    try:
        data = request.get_json()
        numero_processo = data['numero_processo']
        database.marcar_como_arquivado(numero_processo)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Erro ao arquivar: {e}"}), 500

@app.route('/painel', methods=['GET'])
@jwt_required()
def get_painel_endpoint():
    dados_painel = database.buscar_painel_dados()
    return jsonify(dados_painel)

@app.route('/historico', methods=['GET'])
@jwt_required()
def get_historico_endpoint():
    historico = database.buscar_historico_arquivado()
    return jsonify(historico)
    
@app.route('/export-excel', methods=['GET'])
@jwt_required()
def export_excel_endpoint():
    try:
        dados_painel = database.buscar_painel_dados()
        dados_historico = database.buscar_historico_arquivado()
        workbook = Workbook()
        sheet_painel = workbook.active
        sheet_painel.title = "Painel de Controle"
        headers_painel = ["ID", "Responsável", "Processo", "Classificação", "Status", "Última Verificação"]
        sheet_painel.append(headers_painel)
        for processo in dados_painel:
            sheet_painel.append([
                processo['id'], processo['responsavel_principal'], processo['numero_processo'],
                processo['classificacao'], processo['status_geral'], processo['data_ultima_atualizacao']
            ])
        if dados_historico:
            sheet_historico = workbook.create_sheet(title="Histórico")
            headers_historico = ["ID", "Responsável", "Processo", "Classificação", "Data de Arquivamento"]
            sheet_historico.append(headers_historico)
            for processo in dados_historico:
                sheet_historico.append([
                    processo['id'], processo['responsavel_principal'], processo['numero_processo'],
                    processo['classificacao'], processo['data_ultima_atualizacao']
                ])
        excel_buffer = BytesIO()
        workbook.save(excel_buffer)
        excel_buffer.seek(0)
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