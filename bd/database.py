import sqlite3
import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'rpa_dados.db'

# --- Funções Auxiliares (Mantidas) ---
def _limpar_numero(numero_processo_bruto: str) -> str:
    return re.sub(r'\D', '', numero_processo_bruto)

# --- Estrutura do Banco de Dados (Mantida) ---
def inicializar_banco():
    """Cria ou atualiza as tabelas do banco, incluindo a nova tabela de visualização por usuário."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela 1: Processos (sem 'status_geral', pois agora é por usuário)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT UNIQUE,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_ultima_atualizacao TIMESTAMP,
            responsavel_principal TEXT,
            classificacao TEXT
        )
    ''')
    
    # Tabela 2: Subsídios (Mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subsidios_atuais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT,
            item TEXT,
            status TEXT,
            data_atualizacao TIMESTAMP,
            UNIQUE(numero_processo, item)
        )
    ''')
    
    # Tabela 3: Itens Relevantes (Mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_relevantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_nome TEXT UNIQUE
        )
    ''')

    # Tabela 4: Usuários (Mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')

    # Tabela 5: Preferências de Itens por Usuário (Mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_item_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            is_enabled BOOLEAN NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES itens_relevantes (id) ON DELETE CASCADE,
            UNIQUE(user_id, item_id)
        )
    ''')

    # Tabela 6: Associação de Usuários e Processos (Mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_process_view (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            process_id INTEGER NOT NULL,
            status_visualizacao TEXT NOT NULL, -- 'monitorando', 'pendente_ciencia', 'arquivado'
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (process_id) REFERENCES processos (id) ON DELETE CASCADE,
            UNIQUE(user_id, process_id)
        )
    ''')

    conn.commit()
    
    # Garante usuários padrão
    if not buscar_usuario_por_nome('admin'):
        adicionar_usuario('admin', 'admin', role='admin')
    if not buscar_usuario_por_nome('mdr'):
        adicionar_usuario("mdr", "mdr.123")
    
    conn.close()
    print("✔️ Banco de dados (re)inicializado com a estrutura de visualização por usuário.")

# --- Funções de Usuários (Mantidas) ---
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
    usuarios = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return usuarios

# --- Funções de Processo (Mantidas) ---

def associar_processos_usuario(user_id: int, processos_com_dados: list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    
    for processo_info in processos_com_dados:
        numero_limpo = _limpar_numero(processo_info['numero'])
        
        cursor.execute("SELECT id FROM processos WHERE numero_processo = ?", (numero_limpo,))
        processo_existente = cursor.fetchone()
        
        if processo_existente:
            process_id = processo_existente[0]
            cursor.execute("UPDATE processos SET responsavel_principal = ?, classificacao = ? WHERE id = ?",
                           (processo_info['responsavel'], processo_info['classificacao'], process_id))
        else:
            cursor.execute(
                "INSERT INTO processos (numero_processo, responsavel_principal, classificacao, data_ultima_atualizacao) VALUES (?, ?, ?, ?)",
                (numero_limpo, processo_info['responsavel'], processo_info['classificacao'], agora)
            )
            process_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO user_process_view (user_id, process_id, status_visualizacao)
            VALUES (?, ?, 'monitorando')
            ON CONFLICT(user_id, process_id) DO UPDATE SET
                status_visualizacao = 'monitorando';
            """,
            (user_id, process_id)
        )
    
    conn.commit()
    conn.close()


# ==================================================================
#               MUDANÇA PRINCIPAL AQUI
# ==================================================================
def _todos_relevantes_satisfeitos(itens_relevantes_usuario, subsidios_concluidos_encontrados):
    """
    Nova função auxiliar com lógica de verificação flexível.
    Verifica se para cada item relevante, existe um subsídio concluído que o contenha.
    """
    if not itens_relevantes_usuario:
        return False

    for item_relevante in itens_relevantes_usuario:
        satisfeito = False
        for subsidio_concluido in subsidios_concluidos_encontrados:
            # A MÁGICA ACONTECE AQUI:
            # Verifica se o texto do item relevante contém o texto do subsídio, ou vice-versa.
            if item_relevante in subsidio_concluido or subsidio_concluido in item_relevante:
                satisfeito = True
                break  # Encontrou uma correspondência, pode ir para o próximo item relevante
        
        if not satisfeito:
            return False # Se um único item relevante não foi encontrado, a verificação falha

    return True # Se todas as iterações terminaram, todos os itens foram satisfeitos


def atualizar_status_para_usuarios(numero_processo: str, lista_subsidios: list):
    """
    Atualiza subsídios e, para CADA usuário, verifica com a nova lógica flexível
    se os seus itens relevantes foram concluídos para mudar o status.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_processo_limpo = _limpar_numero(numero_processo)

    for subsidio in lista_subsidios:
        cursor.execute(
            "INSERT INTO subsidios_atuais (numero_processo, item, status, data_atualizacao) VALUES (?, ?, ?, ?) ON CONFLICT(numero_processo, item) DO UPDATE SET status=excluded.status, data_atualizacao=excluded.data_atualizacao",
            (numero_processo_limpo, subsidio['item'], subsidio['status'], agora)
        )
    cursor.execute("UPDATE processos SET data_ultima_atualizacao = ? WHERE numero_processo = ?", (agora, numero_processo_limpo))
    conn.commit()
    
    cursor.execute("SELECT id FROM processos WHERE numero_processo = ?", (numero_processo_limpo,))
    process_row = cursor.fetchone()
    if not process_row: return
    process_id = process_row[0]

    cursor.execute("SELECT user_id FROM user_process_view WHERE process_id = ? AND status_visualizacao = 'monitorando'", (process_id,))
    user_ids_monitorando = [row[0] for row in cursor.fetchall()]

    subsidios_concluidos_encontrados = {s['item'] for s in lista_subsidios if s['status'].lower() in ('concluído', 'concluido')}

    for user_id in user_ids_monitorando:
        cursor.execute("""
            SELECT ir.item_nome FROM user_item_preferences uip
            JOIN itens_relevantes ir ON uip.item_id = ir.id
            WHERE uip.user_id = ? AND uip.is_enabled = 1
        """, (user_id,))
        itens_relevantes_usuario = {row[0] for row in cursor.fetchall()}

        # USA A NOVA FUNÇÃO DE VERIFICAÇÃO FLEXÍVEL
        if _todos_relevantes_satisfeitos(itens_relevantes_usuario, subsidios_concluidos_encontrados):
            cursor.execute(
                "UPDATE user_process_view SET status_visualizacao = 'pendente_ciencia' WHERE user_id = ? AND process_id = ?",
                (user_id, process_id)
            )
            print(f"  -> Processo {numero_processo_limpo} agora está 'Pendente Ciência' para o usuário ID {user_id}.")

    conn.commit()
    conn.close()
# ==================================================================


def marcar_ciencia_usuario(user_id: int, numero_processo: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    numero_processo_limpo = _limpar_numero(numero_processo)
    
    cursor.execute("""
        UPDATE user_process_view
        SET status_visualizacao = 'arquivado'
        WHERE user_id = ? AND process_id = (SELECT id FROM processos WHERE numero_processo = ?)
    """, (user_id, numero_processo_limpo))
    
    conn.commit()
    conn.close()

def buscar_painel_usuario(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            p.id, p.numero_processo, p.responsavel_principal, p.classificacao, p.data_ultima_atualizacao,
            v.status_visualizacao AS status_geral
        FROM processos p
        JOIN user_process_view v ON p.id = v.process_id
        WHERE v.user_id = ? AND v.status_visualizacao IN ('monitorando', 'pendente_ciencia')
        ORDER BY p.data_ultima_atualizacao DESC
    """, (user_id,))
    
    dados_painel = [dict(row) for row in cursor.fetchall()]
    
    for processo in dados_painel:
        cursor.execute( "SELECT item, status FROM subsidios_atuais WHERE numero_processo = ? ORDER BY id", (processo['numero_processo'],))
        processo['subsidios'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return dados_painel

def buscar_processos_em_monitoramento_geral() -> list:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT p.numero_processo
        FROM processos p
        JOIN user_process_view v ON p.id = v.process_id
        WHERE v.status_visualizacao = 'monitorando'
    """)
    processos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return processos

def buscar_historico_usuario(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, p.numero_processo, p.responsavel_principal, p.classificacao, p.data_ultima_atualizacao
        FROM processos p
        JOIN user_process_view v ON p.id = v.process_id
        WHERE v.user_id = ? AND v.status_visualizacao = 'arquivado'
        ORDER BY p.data_ultima_atualizacao DESC
    """, (user_id,))
    
    historico = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return historico

# --- Funções de Itens e Preferências (Mantidas) ---
def buscar_itens_relevantes():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_nome FROM itens_relevantes ORDER BY item_nome")
    itens = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return itens

def salvar_itens_relevantes(itens: list):
    """
    Apaga a lista antiga e salva a nova lista de itens relevantes.
    Agora, ignora duplicatas na lista de entrada para evitar erros.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # 1. Apaga a lista antiga para garantir que a nova lista seja a única referência
        cursor.execute("DELETE FROM itens_relevantes")
        
        # 2. Remove duplicatas da lista de entrada antes de inserir
        itens_unicos = sorted(list(set(item.strip() for item in itens if item.strip())))
        
        # 3. Converte para o formato de tupla necessário para a inserção
        itens_tuplas = [(item,) for item in itens_unicos]

        # 4. Insere os itens únicos no banco de dados
        if itens_tuplas:
            cursor.executemany("INSERT INTO itens_relevantes (item_nome) VALUES (?)", itens_tuplas)
        
        conn.commit()
        print(f"✔️ Lista de itens relevantes salva com {len(itens_unicos)} itens únicos.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao salvar itens relevantes: {e}")
    finally:
        conn.close()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM itens_relevantes")
        if itens:
            itens_tuplas = [(item.strip(),) for item in itens if item.strip()]
            cursor.executemany("INSERT INTO itens_relevantes (item_nome) VALUES (?)", itens_tuplas)
        conn.commit()
    finally:
        conn.close()

def get_itens_com_preferencias_usuario(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_item_preferences (user_id, item_id) SELECT ?, id FROM itens_relevantes WHERE id NOT IN (SELECT item_id FROM user_item_preferences WHERE user_id = ?)", (user_id, user_id))
    conn.commit()
    cursor.execute("SELECT ir.id, ir.item_nome, uip.is_enabled FROM itens_relevantes ir JOIN user_item_preferences uip ON ir.id = uip.item_id WHERE uip.user_id = ?", (user_id,))
    itens = [{'id': row[0], 'item_nome': row[1], 'is_enabled': bool(row[2])} for row in cursor.fetchall()]
    conn.close()
    return itens

def atualizar_preferencia_usuario(user_id: int, item_id: int, is_enabled: bool):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_item_preferences SET is_enabled = ? WHERE user_id = ? AND item_id = ?", (1 if is_enabled else 0, user_id, item_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    inicializar_banco()