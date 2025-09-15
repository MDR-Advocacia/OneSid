import sqlite3
import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash
import unicodedata # Importe esta biblioteca no topo do arquivo

DB_NAME = 'rpa_dados.db'

# --- Funções Auxiliares ---
def _limpar_numero(numero_processo_bruto: str) -> str:
    """Remove todos os caracteres não numéricos de uma string."""
    return re.sub(r'\D', '', numero_processo_bruto)

# ==================================================================
#               NOVA FUNÇÃO DE LIMPEZA ROBUSTA
# ==================================================================
def _normalize_string(text: str) -> str:
    """
    Função de limpeza que converte para minúsculo, remove acentos,
    caracteres especiais e espaços extras. Garante uma comparação confiável.
    """
    if not isinstance(text, str):
        return ""
    # Remove acentos
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    # Converte para minúsculas
    text = text.lower()
    # Remove caracteres especiais (mantém apenas letras, números e espaços)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # Remove espaços duplicados e no início/fim
    return re.sub(r'\s+', ' ', text).strip()

# --- Estrutura do Banco de Dados ---
def inicializar_banco():
    """Cria ou atualiza as tabelas do banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, numero_processo TEXT UNIQUE, status_geral TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, data_ultima_atualizacao TIMESTAMP,
            responsavel_principal TEXT, classificacao TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subsidios_atuais (
            id INTEGER PRIMARY KEY AUTOINCREMENT, numero_processo TEXT, item TEXT, status TEXT,
            data_atualizacao TIMESTAMP, UNIQUE(numero_processo, item)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_relevantes (id INTEGER PRIMARY KEY AUTOINCREMENT, item_nome TEXT UNIQUE)
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_item_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_id INTEGER NOT NULL,
            is_enabled BOOLEAN NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES itens_relevantes (id) ON DELETE CASCADE,
            UNIQUE(user_id, item_id)
        )
    ''')
    
    conn.commit()

    if not buscar_usuario_por_nome('admin'):
        adicionar_usuario('admin', 'admin', role='admin')
    if not buscar_usuario_por_nome('mdr'):
        adicionar_usuario("mdr", "mdr.123")

    conn.close()
    print("✔️ Banco de dados (re)inicializado com a estrutura de permissões.")

# --- Funções de Usuários e Permissões ---
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

# --- Funções de Processos e Subsídios ---
def adicionar_processos_para_monitorar(processos_com_dados: list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    for processo_info in processos_com_dados:
        numero_limpo = _limpar_numero(processo_info['numero'])
        cursor.execute(
            "INSERT INTO processos (numero_processo, responsavel_principal, classificacao, status_geral, data_ultima_atualizacao) VALUES (?, ?, ?, ?, ?) ON CONFLICT(numero_processo) DO UPDATE SET responsavel_principal = excluded.responsavel_principal, classificacao = excluded.classificacao;",
            (numero_limpo, processo_info['responsavel'], processo_info['classificacao'], 'Em Monitoramento', agora)
        )
    conn.commit()
    conn.close()

def _todos_relevantes_satisfeitos(itens_relevantes_usuario, subsidios_concluidos_encontrados):
    if not itens_relevantes_usuario: return False
    norm_relevantes = {_normalize_string(item) for item in itens_relevantes_usuario}
    norm_concluidos = {_normalize_string(item) for item in subsidios_concluidos_encontrados}
    for item_relevante in norm_relevantes:
        satisfeito = any(item_relevante in subsidio_concluido or subsidio_concluido in item_relevante for subsidio_concluido in norm_concluidos)
        if not satisfeito: return False
    return True

def atualizar_status_processo(numero_processo: str, lista_subsidios: list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_processo_limpo = _limpar_numero(numero_processo)

    for subsidio in lista_subsidios:
        cursor.execute(
            "INSERT INTO subsidios_atuais (numero_processo, item, status, data_atualizacao) VALUES (?, ?, ?, ?) ON CONFLICT(numero_processo, item) DO UPDATE SET status = excluded.status, data_atualizacao = excluded.data_atualizacao;",
            (numero_processo_limpo, subsidio['item'], subsidio['status'], agora)
        )
    
    # Busca os itens relevantes PARA CADA USUÁRIO e atualiza se necessário
    cursor.execute("SELECT id FROM users")
    todos_user_ids = [row[0] for row in cursor.fetchall()]

    subsidios_concluidos_encontrados = {s['item'] for s in lista_subsidios if s['status'].lower() in ('concluído', 'concluido')}

    for user_id in todos_user_ids:
        cursor.execute("""
            SELECT ir.item_nome FROM user_item_preferences uip
            JOIN itens_relevantes ir ON uip.item_id = ir.id
            WHERE uip.user_id = ? AND uip.is_enabled = 1
        """, (user_id,))
        itens_relevantes_usuario = {row[0] for row in cursor.fetchall()}

        if _todos_relevantes_satisfeitos(itens_relevantes_usuario, subsidios_concluidos_encontrados):
            # Esta parte precisaria ser adaptada se o status fosse por usuário, mas mantendo a lógica global por enquanto.
            status_geral_novo = 'Pendente Ciencia'
            cursor.execute(
                "UPDATE processos SET status_geral = ?, data_ultima_atualizacao = ? WHERE numero_processo = ?",
                (status_geral_novo, agora, numero_processo_limpo)
            )
            print(f"  -> Processo {numero_processo_limpo} atualizado para 'Pendente Ciencia'.")
            break # Atualiza para o primeiro usuário que satisfaz e para
    
    conn.commit()
    conn.close()

def marcar_como_arquivado(numero_processo: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_processo_limpo = _limpar_numero(numero_processo)
    cursor.execute("UPDATE processos SET status_geral = ?, data_ultima_atualizacao = ? WHERE numero_processo = ?", ('Arquivado', agora, numero_processo_limpo))
    conn.commit()
    conn.close()

def buscar_painel_dados():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, numero_processo, responsavel_principal, classificacao, status_geral, data_ultima_atualizacao FROM processos WHERE status_geral != 'Arquivado' ORDER BY data_ultima_atualizacao DESC")
    dados_painel = [dict(row) for row in cursor.fetchall()]
    for processo in dados_painel:
        cursor.execute("SELECT item, status FROM subsidios_atuais WHERE numero_processo = ? ORDER BY id", (processo['numero_processo'],))
        processo['subsidios'] = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return dados_painel

def buscar_processos_em_monitoramento() -> list:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT numero_processo FROM processos WHERE status_geral = 'Em Monitoramento'")
    return [row[0] for row in cursor.fetchall()]

def buscar_historico_arquivado():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, numero_processo, responsavel_principal, classificacao, data_ultima_atualizacao FROM processos WHERE status_geral = 'Arquivado' ORDER BY data_ultima_atualizacao DESC")
    return [dict(row) for row in cursor.fetchall()]

def buscar_itens_relevantes():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_nome FROM itens_relevantes ORDER BY item_nome")
    return [dict(row) for row in cursor.fetchall()]

# ==================================================================
#               FUNÇÃO DE SALVAR CORRIGIDA
# ==================================================================
def salvar_itens_relevantes(itens: list):
    """
    Apaga a lista antiga e salva a nova, removendo duplicatas
    para evitar erros de 'UNIQUE constraint'.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM itens_relevantes")
        itens_unicos = sorted(list(set(item.strip() for item in itens if item.strip())))
        itens_tuplas = [(item,) for item in itens_unicos]
        if itens_tuplas:
            cursor.executemany("INSERT INTO itens_relevantes (item_nome) VALUES (?)", itens_tuplas)
        conn.commit()
        print(f"✔️ Lista de itens relevantes salva com {len(itens_unicos)} itens únicos.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao salvar itens relevantes: {e}")
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