# Substitua todo o conteúdo de RPA/server.py por este código:

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import check_password_hash
import sys
import os
from datetime import timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import bd.database as database
import apexFluxoLegalOne 

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key-for-dev')
#app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:3001", "http://192.168.0.66:3000", "http://192.168.0.66:3001"]}})
#database.inicializar_banco()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = database.buscar_usuario_por_nome(username)
    if user and check_password_hash(user['password_hash'], password):
        session.permanent = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        return jsonify({"message": "Login bem-sucedido", "username": user['username'], "role": user['role']}), 200
    return jsonify({"message": "Credenciais inválidas"}), 401

@app.route('/api/add-process', methods=['POST'])
def add_single_process():
    if 'user_id' not in session:
        return jsonify({"message": "Acesso não autorizado"}), 401
    data = request.get_json()
    numero_processo = data.get('numero_processo')
    executante = data.get('executante', '')
    if not numero_processo or not numero_processo.strip():
        return jsonify({"message": "O número do processo é obrigatório"}), 400
    user_id = session['user_id']
    try:
        processo_id = database.adicionar_processo_unitario(user_id, numero_processo, executante)
        if processo_id:
            return jsonify({"message": "Processo colocado na esteira de monitoramento!", "process_id": processo_id}), 201
        return jsonify({"message": "Falha ao adicionar processo."}), 500
    except Exception as e:
        return jsonify({"message": f"Erro interno do servidor: {e}"}), 500

@app.route('/api/import-legal-one', methods=['POST'])
def import_from_legal_one():
    if 'user_id' not in session:
        return jsonify({"message": "Acesso não autorizado"}), 401
    user_id = session['user_id']
    try:
        tarefas_importadas = apexFluxoLegalOne.main()
        if not tarefas_importadas:
            return jsonify({"message": "Nenhuma tarefa nova encontrada no Legal One."}), 200
        processos_adicionados = 0
        processos_ignorados = 0
        for tarefa in tarefas_importadas:
            numero_cnj = tarefa.get('processo_cnj')
            nome_responsavel = tarefa.get('finalizado_por_nome')
            tarefa_id = tarefa.get('tarefa_id')
            # --- MUDANÇA AQUI ---
            # Pegamos também o ID do responsável
            id_responsavel = tarefa.get('finalizado_por_id')
            
            if numero_cnj and tarefa_id:
                # E passamos para a função do banco
                resultado = database.adicionar_processo_unitario(user_id, numero_cnj, nome_responsavel, tarefa_id=tarefa_id, id_responsavel=id_responsavel)
                if resultado is not None:
                    processos_adicionados += 1
                else:
                    processos_ignorados += 1
        
        mensagem = f"Importação finalizada! {processos_adicionados} novos processos adicionados. {processos_ignorados} já existentes foram ignorados."
        return jsonify({"message": mensagem}), 201
    except Exception as e:
        return jsonify({"message": f"Ocorreu um erro durante a importação: {e}"}), 500

# --- NOVA ROTA DE EXPORTAÇÃO ---
@app.route('/api/exportar-json', methods=['GET'])
def exportar_json():
    if 'user_id' not in session:
        return jsonify({"message": "Acesso não autorizado"}), 401
    
    try:
        # Chama a nova função do banco de dados
        lista_processos = database.exportar_dados_json()
        
        # Monta o objeto final no formato solicitado
        resultado_final = {
            "fonte": "Onesid",
            "processos": lista_processos
        }
        
        return jsonify(resultado_final), 200
    except Exception as e:
        print(f"Erro ao exportar JSON: {e}")
        return jsonify({"message": "Erro interno ao gerar o JSON."}), 500


# (O restante das rotas permanece o mesmo)
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logout bem-sucedido"}), 200

@app.route('/api/profile')
def profile():
    if 'user_id' in session:
        return jsonify({"logged_in": True, "user_id": session['user_id'], "username": session['username'], "role": session.get('role', 'user')})
    return jsonify({"logged_in": False}), 401
    
@app.route('/api/painel')
def get_painel():
    if 'user_id' not in session:
        return jsonify({"message": "Acesso não autorizado"}), 401
    user_id = session['user_id']
    return jsonify(database.buscar_painel_usuario(user_id))

@app.route('/api/historico')
def get_historico():
    if 'user_id' not in session:
        return jsonify({"message": "Acesso não autorizado"}), 401
    user_id = session['user_id']
    return jsonify(database.buscar_historico_usuario(user_id))

@app.route('/api/marcar-ciencia', methods=['POST'])
def marcar_ciencia():
    if 'user_id' not in session:
        return jsonify({"message": "Acesso não autorizado"}), 401
    data = request.get_json()
    numero_processo = data.get('numero_processo')
    if not numero_processo:
        return jsonify({"message": "Número do processo não fornecido"}), 400
    database.marcar_ciencia_global(numero_processo)
    return jsonify({"message": "Processo arquivado com sucesso para todos os usuários."}), 200

@app.route('/api/delete-process/<int:process_id>', methods=['DELETE'])
def delete_process(process_id):
    # 1. Verifica se o usuário está logado
    if 'user_id' not in session:
        return jsonify({"message": "Acesso não autorizado"}), 401
    
    # 2. Verifica se o usuário é admin
    if session.get('role') != 'admin':
        return jsonify({"message": "Acesso restrito a administradores"}), 403
        
    try:
        if database.excluir_processo_por_id(process_id):
            return jsonify({"message": "Processo excluído com sucesso."}), 200
        else:
            return jsonify({"message": "Não foi possível excluir o processo."}), 500
    except Exception as e:
        return jsonify({"message": f"Erro interno: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)