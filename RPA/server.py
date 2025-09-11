import sys
import os
import traceback
from functools import wraps
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity
from openpyxl import Workbook
from io import BytesIO

# --- CORREÇÃO DO CAMINHO DE IMPORTAÇÃO (mantido) ---
caminho_atual = os.path.dirname(os.path.abspath(__file__))
caminho_raiz_do_projeto = os.path.dirname(caminho_atual)
sys.path.append(caminho_raiz_do_projeto)
# -----------------------------------------

import main
from bd import database

# Inicializa o banco de dados com a estrutura mais recente
database.inicializar_banco()

app = Flask(__name__)

# --- CONFIGURAÇÕES DA APLICAÇÃO ---
# DICA DE SEGURANÇA: É melhor carregar isso de uma variável de ambiente
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "uma-chave-super-secreta-e-diferente")
CORS(app)
jwt = JWTManager(app)
# --- FIM DAS CONFIGURAÇÕES ---


# --- DECORADOR DE PERMISSÃO DE ADMIN ---
def admin_required():
    """Decorador que protege uma rota, permitindo acesso apenas a usuários com role 'admin'."""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            current_username = get_jwt_identity()
            user = database.buscar_usuario_por_nome(current_username)
            if user and user.get('role') == 'admin':
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="Acesso restrito a administradores!"), 403
        return decorator
    return wrapper
# --- FIM DO DECORADOR ---


# --- ROTA DE LOGIN (ATUALIZADA) ---
@app.route('/login', methods=['POST'])
def login_endpoint():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = database.buscar_usuario_por_nome(username)
    
    # Verifica se o usuário existe e se a senha está correta
    if user and check_password_hash(user['password_hash'], password):
        # Cria o token de acesso
        access_token = create_access_token(identity=username)
        # Retorna o token E a permissão (role) do usuário
        return jsonify(access_token=access_token, role=user.get('role', 'user'))
    
    return jsonify({"msg": "Usuário ou senha inválidos"}), 401
# --- FIM DA ROTA DE LOGIN ---


# --- ROTAS DE ITENS (ADMIN E USUÁRIO) ---

# Rota para buscar a lista mestre de itens (acessível por todos os usuários logados)
@app.route('/itens-relevantes', methods=['GET'])
@jwt_required()
def get_itens_relevantes():
    try:
        itens = database.buscar_itens_relevantes()
        return jsonify(itens)
    except Exception as e:
        return jsonify({"error": f"Erro: {e}"}), 500

# Rota para ADMIN salvar/atualizar a lista mestre de itens
@app.route('/itens-relevantes', methods=['POST'])
@jwt_required()
@admin_required() # <-- Apenas admins podem acessar
def post_itens_relevantes():
    try:
        data = request.get_json()
        itens = data['itens']
        database.salvar_itens_relevantes(itens)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Erro: {e}"}), 500

# NOVA Rota para um USUÁRIO obter a lista de itens com SUAS preferências
@app.route('/preferencias-usuario', methods=['GET'])
@jwt_required()
def get_user_preferences():
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user:
            return jsonify({"msg": "Usuário não encontrado"}), 404
        
        preferences = database.get_itens_com_preferencias_usuario(user['id'])
        return jsonify(preferences)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro ao buscar preferências: {e}"}), 500

# NOVA Rota para um USUÁRIO habilitar ou desabilitar um item
@app.route('/preferencias-usuario', methods=['PUT'])
@jwt_required()
def update_user_preference():
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user:
            return jsonify({"msg": "Usuário não encontrado"}), 404
        
        data = request.get_json()
        item_id = data.get('item_id')
        is_enabled = data.get('is_enabled')

        if item_id is None or not isinstance(is_enabled, bool):
            return jsonify({"msg": "Parâmetros 'item_id' e 'is_enabled' (booleano) são obrigatórios."}), 400
            
        database.atualizar_preferencia_usuario(user['id'], item_id, is_enabled)
        return jsonify({"success": True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro ao atualizar preferência: {e}"}), 500

# --- ROTAS DE PROCESSOS E RPA (sem alterações de lógica) ---

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
    
# --- NOVAS ROTAS PARA GERENCIAMENTO DE USUÁRIOS (Admin) ---

@app.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_users():
    """Retorna uma lista de todos os usuários (sem as senhas)."""
    try:
        users = database.listar_todos_usuarios()
        return jsonify(users)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro ao buscar usuários: {e}"}), 500

@app.route('/users', methods=['POST'])
@jwt_required()
@admin_required()
def create_user():
    """Cria um novo usuário."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user') # O padrão é 'user' se não for especificado

    if not username or not password:
        return jsonify({"msg": "Nome de usuário e senha são obrigatórios."}), 400
    
    # Verifica se o usuário já existe
    if database.buscar_usuario_por_nome(username):
        return jsonify({"msg": f"O nome de usuário '{username}' já está em uso."}), 409 # 409 Conflict

    try:
        database.adicionar_usuario(username, password, role)
        return jsonify({"success": True, "msg": f"Usuário '{username}' criado com sucesso."}), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro ao criar usuário: {e}"}), 500

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