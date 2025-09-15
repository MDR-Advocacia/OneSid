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
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "uma-chave-super-secreta-e-diferente")
CORS(app)
jwt = JWTManager(app)

# --- DECORADOR DE PERMISSÃO DE ADMIN (mantido) ---
def admin_required():
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

# --- ROTA DE LOGIN (mantida) ---
@app.route('/login', methods=['POST'])
def login_endpoint():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = database.buscar_usuario_por_nome(username)
    
    if user and check_password_hash(user['password_hash'], password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token, role=user.get('role', 'user'))
    
    return jsonify({"msg": "Usuário ou senha inválidos"}), 401

# --- ROTAS DE ITENS E PREFERÊNCIAS (mantidas) ---
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
@admin_required()
def post_itens_relevantes():
    try:
        data = request.get_json()
        itens = data['itens']
        database.salvar_itens_relevantes(itens)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Erro: {e}"}), 500
    

@app.route('/importar-itens', methods=['POST'])
@jwt_required()
@admin_required()
def importar_itens_relevantes():
    """
    Recebe um arquivo .txt, lê cada linha como um item e salva no banco de dados,
    substituindo a lista antiga.
    """
    # Verifica se um arquivo foi enviado na requisição
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400
    
    file = request.files['file']

    # Verifica se o nome do arquivo não está vazio
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    # Verifica se é um arquivo de texto
    if file and file.filename.endswith('.txt'):
        try:
            # Lê o conteúdo do arquivo e decodifica para string
            content = file.read().decode('utf-8')
            # Separa a string em uma lista, onde cada linha é um item
            itens = content.splitlines()
            # Remove linhas vazias que possam existir
            itens_limpos = [item.strip() for item in itens if item.strip()]
            
            # Usa a mesma função que já tínhamos para salvar no banco
            database.salvar_itens_relevantes(itens_limpos)
            
            # Retorna a lista atualizada para o frontend
            itens_atualizados = database.buscar_itens_relevantes()
            return jsonify({
                "success": True, 
                "msg": f"{len(itens_limpos)} itens importados com sucesso!",
                "itens": itens_atualizados
            })
        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": f"Erro ao processar o arquivo: {e}"}), 500

    return jsonify({"error": "Formato de arquivo inválido. Por favor, envie um arquivo .txt"}), 400



@app.route('/preferencias-usuario', methods=['GET'])
@jwt_required()
def get_user_preferences():
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user: return jsonify({"msg": "Usuário não encontrado"}), 404
        preferences = database.get_itens_com_preferencias_usuario(user['id'])
        return jsonify(preferences)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar preferências: {e}"}), 500

@app.route('/preferencias-usuario', methods=['PUT'])
@jwt_required()
def update_user_preference():
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user: return jsonify({"msg": "Usuário não encontrado"}), 404
        data = request.get_json()
        item_id, is_enabled = data.get('item_id'), data.get('is_enabled')
        if item_id is None or not isinstance(is_enabled, bool):
            return jsonify({"msg": "Parâmetros 'item_id' e 'is_enabled' (booleano) são obrigatórios."}), 400
        database.atualizar_preferencia_usuario(user['id'], item_id, is_enabled)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Erro ao atualizar preferência: {e}"}), 500
        
# --- ROTAS DE USUÁRIOS (Admin - mantidas) ---
@app.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_users():
    users = database.listar_todos_usuarios()
    return jsonify(users)

@app.route('/users', methods=['POST'])
@jwt_required()
@admin_required()
def create_user():
    data = request.get_json()
    username, password, role = data.get('username'), data.get('password'), data.get('role', 'user')
    if not username or not password:
        return jsonify({"msg": "Nome de usuário e senha são obrigatórios."}), 400
    if database.buscar_usuario_por_nome(username):
        return jsonify({"msg": f"O nome de usuário '{username}' já está em uso."}), 409
    database.adicionar_usuario(username, password, role)
    return jsonify({"success": True, "msg": f"Usuário '{username}' criado com sucesso."}), 201

# --- ROTAS DE PROCESSOS E RPA (CORRIGIDAS) ---

@app.route('/add-processes', methods=['POST'])
@jwt_required()
def add_processes_endpoint():
    """Ação ÚNICA: Apenas associa os processos ao usuário no banco."""
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user: 
            return jsonify({"msg": "Usuário não encontrado"}), 404

        data = request.get_json()
        processos_com_dados = data.get('processos', [])
        
        database.associar_processos_usuario(user['id'], processos_com_dados)
        
        return jsonify({"success": True, "msg": "Processos adicionados à fila de monitoramento."})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro ao adicionar processos: {e}"}), 500

# A rota /run-monitoring agora é única e tem a lógica correta
@app.route('/run-monitoring', methods=['POST'])
@jwt_required()
def run_monitoring_endpoint():
    """Roda o monitoramento para todos os processos que algum usuário esteja monitorando (Admin)."""
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user: return jsonify({"msg": "Usuário não encontrado"}), 404
        
        processos_para_rodar = database.buscar_processos_em_monitoramento_geral()
        
        if processos_para_rodar:
            main.executar_rpa(processos_para_rodar, database.atualizar_status_para_usuarios)
        
        dados_painel = database.buscar_painel_usuario(user['id'])
        return jsonify(dados_painel)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/dar-ciencia', methods=['POST'])
@jwt_required()
def dar_ciencia_endpoint():
    """Marca um processo como 'arquivado' na visão do usuário logado."""
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user: return jsonify({"msg": "Usuário não encontrado"}), 404
        
        data = request.get_json()
        numero_processo = data['numero_processo']
        
        database.marcar_ciencia_usuario(user['id'], numero_processo)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Erro ao dar ciência: {e}"}), 500

@app.route('/painel', methods=['GET'])
@jwt_required()
def get_painel_endpoint():
    """Busca os dados do painel para o usuário logado."""
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user: return jsonify({"msg": "Usuário não encontrado"}), 404
        
        dados_painel = database.buscar_painel_usuario(user['id'])
        return jsonify(dados_painel)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro: {e}"}), 500

@app.route('/historico', methods=['GET'])
@jwt_required()
def get_historico_endpoint():
    """Busca o histórico de processos para o usuário logado."""
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user: return jsonify({"msg": "Usuário não encontrado"}), 404
        
        historico = database.buscar_historico_usuario(user['id'])
        return jsonify(historico)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro: {e}"}), 500
    
@app.route('/export-excel', methods=['GET'])
@jwt_required()
def export_excel_endpoint():
    """Exporta para Excel a visão do painel e histórico do usuário logado."""
    try:
        current_username = get_jwt_identity()
        user = database.buscar_usuario_por_nome(current_username)
        if not user: return jsonify({"msg": "Usuário não encontrado"}), 404
        
        dados_painel = database.buscar_painel_usuario(user['id'])
        dados_historico = database.buscar_historico_usuario(user['id'])
        
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
            excel_buffer, as_attachment=True,
            download_name=f'onesid_export_{current_username}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro ao gerar a planilha: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)