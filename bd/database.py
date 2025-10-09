# Substitua todo o conteúdo de bd/database.py por este código:

import sqlite3
import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash
import unicodedata
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_NAME = os.path.join(PROJECT_ROOT, 'rpa_dados.db')

def _limpar_numero(numero_processo_bruto: str) -> str:
    return re.sub(r'\D', '', numero_processo_bruto)

def _normalize_string(text: str) -> str:
    if not isinstance(text, str): return ""
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def inicializar_banco():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            numero_processo TEXT, 
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            data_ultima_atualizacao TIMESTAMP, 
            responsavel_principal TEXT, 
            classificacao TEXT,
            tarefa_id INTEGER UNIQUE,
            id_responsavel INTEGER
        )
    ''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS subsidios_atuais (id INTEGER PRIMARY KEY AUTOINCREMENT, numero_processo TEXT, item TEXT, status TEXT, data_atualizacao TIMESTAMP, UNIQUE(numero_processo, item))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS itens_relevantes (id INTEGER PRIMARY KEY AUTOINCREMENT, item_nome TEXT UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_item_preferences (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_id INTEGER NOT NULL, is_enabled BOOLEAN NOT NULL DEFAULT 1, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE, FOREIGN KEY (item_id) REFERENCES itens_relevantes (id) ON DELETE CASCADE, UNIQUE(user_id, item_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_process_view (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, process_id INTEGER NOT NULL, status_visualizacao TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE, FOREIGN KEY (process_id) REFERENCES processos (id) ON DELETE CASCADE, UNIQUE(user_id, process_id))''')
    conn.commit()
    if not buscar_usuario_por_nome('admin'):
        adicionar_usuario('admin', 'admin', role='admin')
    if not buscar_usuario_por_nome('mdr'):
        adicionar_usuario("mdr", "mdr.123")
    conn.close()
    print("✔️ Banco de dados (re)inicializado com a estrutura de visualização por usuário.")

def adicionar_processo_unitario(user_id: int, numero_processo: str, executante: str, tarefa_id: int = None, id_responsavel: int = None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_limpo = _limpar_numero(numero_processo)
    try:
        cursor.execute(
            "INSERT INTO processos (numero_processo, responsavel_principal, data_ultima_atualizacao, tarefa_id, id_responsavel) VALUES (?, ?, ?, ?, ?)", 
            (numero_limpo, executante, agora, tarefa_id, id_responsavel)
        )
        process_id = cursor.lastrowid
        if process_id and user_id:
            cursor.execute( "INSERT INTO user_process_view (user_id, process_id, status_visualizacao) VALUES (?, ?, 'monitorando')", (user_id, process_id) )
        conn.commit()
        return process_id
    except sqlite3.IntegrityError:
        print(f"Tarefa ID {tarefa_id} já existe no banco. Ignorando.")
        return None
    except Exception as e:
        print(f"Erro em adicionar_processo_unitario: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

# --- FUNÇÃO DE EXPORTAÇÃO MODIFICADA ---
def exportar_dados_json():
    """
    Busca os dados e agrupa as observações por numero_processo e id_responsavel.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Dicionário para agrupar as observações
    # A chave será uma tupla (numero_processo, id_responsavel)
    # O valor será uma lista de strings de observação
    processos_agrupados = {}
    
    # Busca os processos base que estão sendo monitorados
    cursor.execute("""
        SELECT 
            p.id, p.numero_processo, p.id_responsavel
        FROM processos p 
        JOIN user_process_view v ON p.id = v.process_id 
        WHERE v.status_visualizacao = 'monitorando'
    """)
    processos_base = cursor.fetchall()
    
    for processo in processos_base:
        chave_agrupamento = (processo['numero_processo'], processo['id_responsavel'])
        
        # Se a chave ainda não existe no dicionário, inicializa
        if chave_agrupamento not in processos_agrupados:
            processos_agrupados[chave_agrupamento] = {
                "numero_processo": processo['numero_processo'],
                "id_responsavel": processo['id_responsavel'],
                "observacoes": [] # Usamos uma lista temporária
            }

        # Para cada processo, busca seus subsídios
        cursor.execute("SELECT item, status FROM subsidios_atuais WHERE numero_processo = ?", (processo['numero_processo'],))
        subsidios = cursor.fetchall()
        
        for subsidio in subsidios:
            observacao = f"PROATIVO: {subsidio['item']} ({subsidio['status'].upper()})."
            processos_agrupados[chave_agrupamento]["observacoes"].append(observacao)

    conn.close()

    # Monta a lista final a partir dos dados agrupados
    lista_de_processos_export = []
    for grupo in processos_agrupados.values():
        # Junta todas as observações da lista com " ; "
        observacao_final = " ; ".join(grupo["observacoes"])
        
        lista_de_processos_export.append({
            "numero_processo": grupo["numero_processo"],
            "id_responsavel": grupo["id_responsavel"],
            "observacao": observacao_final
        })
        
    return lista_de_processos_export

# (O restante do arquivo continua o mesmo)
def adicionar_usuario(username, password, role='user'):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, role))
        conn.commit()
    except sqlite3.IntegrityError:
        if role == 'admin':
            cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
            conn.commit()
    finally:
        conn.close()

def buscar_usuario_por_nome(username):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def listar_todos_usuarios():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users ORDER BY username")
    return [dict(row) for row in cursor.fetchall()]

def associar_processos_usuario(user_id: int, processos_com_dados: list):
    conn = sqlite3.connect(DB_NAME)
    for processo_info in processos_com_dados:
        adicionar_processo_unitario(user_id, processo_info['numero'], processo_info['responsavel'])
    conn.close()

def _todos_relevantes_satisfeitos(processo_id, usuario_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT ir.item_nome FROM user_item_preferences uip JOIN itens_relevantes ir ON uip.item_id = ir.id WHERE uip.user_id = ? AND uip.is_enabled = 1", (usuario_id,))
        preferencias_relevantes_nomes = {row[0] for row in cursor.fetchall()}
        if not preferencias_relevantes_nomes: return False
        cursor.execute("SELECT item FROM subsidios_atuais WHERE numero_processo = (SELECT numero_processo FROM processos WHERE id = ?)", (processo_id,))
        itens_no_processo_nomes = {row[0] for row in cursor.fetchall()}
        relevantes_neste_processo_nomes = preferencias_relevantes_nomes.intersection(itens_no_processo_nomes)
        if not relevantes_neste_processo_nomes: return False
        cursor.execute("SELECT item FROM subsidios_atuais WHERE numero_processo = (SELECT numero_processo FROM processos WHERE id = ?) AND (status LIKE 'Concluído' OR status LIKE 'Concluido')", (processo_id,))
        subsidios_concluidos_nomes = {row[0] for row in cursor.fetchall()}
        return relevantes_neste_processo_nomes.issubset(subsidios_concluidos_nomes)
    finally:
        conn.close()

def atualizar_status_para_usuarios(numero_processo: str, lista_subsidios: list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_processo_limpo = _limpar_numero(numero_processo)
    for subsidio in lista_subsidios:
        cursor.execute("INSERT INTO subsidios_atuais (numero_processo, item, status, data_atualizacao) VALUES (?, ?, ?, ?) ON CONFLICT(numero_processo, item) DO UPDATE SET status=excluded.status, data_atualizacao=excluded.data_atualizacao", (numero_processo_limpo, subsidio['item'], subsidio['status'], agora))
    cursor.execute("UPDATE processos SET data_ultima_atualizacao = ? WHERE numero_processo = ?", (agora, numero_processo_limpo))
    conn.commit()
    cursor.execute("SELECT id FROM processos WHERE numero_processo = ?", (numero_processo_limpo,))
    process_row = cursor.fetchone()
    if not process_row: 
        conn.close()
        return
    process_id = process_row[0]
    cursor.execute("SELECT user_id FROM user_process_view WHERE process_id = ? AND status_visualizacao = 'monitorando'", (process_id,))
    user_ids_monitorando = [row[0] for row in cursor.fetchall()]
    for user_id in user_ids_monitorando:
        if _todos_relevantes_satisfeitos(process_id, user_id):
            cursor.execute("UPDATE user_process_view SET status_visualizacao = 'pendente_ciencia' WHERE user_id = ? AND process_id = ?", (user_id, process_id))
    conn.commit()
    conn.close()
    
def marcar_ciencia_global(numero_processo: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    numero_processo_limpo = _limpar_numero(numero_processo)
    try:
        cursor.execute("UPDATE user_process_view SET status_visualizacao = 'arquivado' WHERE process_id = (SELECT id FROM processos WHERE numero_processo = ?)", (numero_processo_limpo,))
        conn.commit()
    finally:
        conn.close()

def buscar_painel_usuario(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            p.id, p.numero_processo, p.responsavel_principal, p.classificacao, 
            p.data_ultima_atualizacao, MIN(v.status_visualizacao) AS status_geral 
        FROM processos p 
        JOIN user_process_view v ON p.id = v.process_id 
        WHERE v.status_visualizacao IN ('monitorando', 'pendente_ciencia') 
        GROUP BY p.id
        ORDER BY p.data_ultima_atualizacao DESC
    """)
    dados_painel = [dict(row) for row in cursor.fetchall()]
    for processo in dados_painel:
        cursor.execute("SELECT item, status FROM subsidios_atuais WHERE numero_processo = ? ORDER BY id", (processo['numero_processo'],))
        processo['subsidios'] = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return dados_painel

def buscar_processos_em_monitoramento_geral() -> list:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT p.numero_processo FROM processos p JOIN user_process_view v ON p.id = v.process_id WHERE v.status_visualizacao = 'monitorando'")
    return [row[0] for row in cursor.fetchall()]

def buscar_historico_usuario(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT p.id, p.numero_processo, p.responsavel_principal, p.classificacao, p.data_ultima_atualizacao FROM processos p JOIN user_process_view v ON p.id = v.process_id WHERE v.user_id = ? AND v.status_visualizacao = 'arquivado' ORDER BY p.data_ultima_atualizacao DESC", (user_id,))
    return [dict(row) for row in cursor.fetchall()]

def buscar_itens_relevantes():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_nome FROM itens_relevantes ORDER BY item_nome")
    return [dict(row) for row in cursor.fetchall()]

def salvar_itens_relevantes(itens: list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM itens_relevantes")
        itens_unicos = sorted(list(set(item.strip() for item in itens if item.strip())))
        itens_tuplas = [(item,) for item in itens_unicos]
        if itens_tuplas:
            cursor.executemany("INSERT INTO itens_relevantes (item_nome) VALUES (?)", itens_tuplas)
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()

def get_itens_com_preferencias_usuario(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_item_preferences (user_id, item_id) SELECT ?, id FROM itens_relevantes WHERE id NOT IN (SELECT item_id FROM user_item_preferences WHERE user_id = ?)", (user_id, user_id))
    conn.commit()
    cursor.execute("SELECT ir.id, ir.item_nome, uip.is_enabled FROM itens_relevantes ir JOIN user_item_preferences uip ON ir.id = uip.item_id WHERE uip.user_id = ?", (user_id,))
    return [{'id': row[0], 'item_nome': row[1], 'is_enabled': bool(row[2])} for row in cursor.fetchall()]

def atualizar_preferencia_usuario(user_id: int, item_id: int, is_enabled: bool):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_item_preferences SET is_enabled = ? WHERE user_id = ? AND item_id = ?", (1 if is_enabled else 0, user_id, item_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    inicializar_banco()