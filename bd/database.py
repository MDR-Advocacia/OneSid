import sqlite3
import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash

# Usando o nome do seu banco de dados
DB_NAME = 'rpa_dados.db'

# --- Funções Auxiliares ---
def _limpar_numero(numero_processo_bruto: str) -> str:
    """Remove todos os caracteres não numéricos de uma string."""
    return re.sub(r'\D', '', numero_processo_bruto)

# --- Estrutura do Banco de Dados ---
def inicializar_banco():
    """Cria ou atualiza as tabelas do banco de dados com a nova estrutura de permissões."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela 1: Processos (Sua estrutura original mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT UNIQUE,
            status_geral TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_ultima_atualizacao TIMESTAMP,
            responsavel_principal TEXT,
            classificacao TEXT
        )
    ''')
    
    # Tabela 2: Subsídios (Sua estrutura original mantida)
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
    
    # Tabela 3: Itens Relevantes (Sua estrutura original mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_relevantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_nome TEXT UNIQUE
        )
    ''')

    # Tabela 4: Usuários (ATUALIZADA com a coluna 'role')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' -- 'user' ou 'admin'
        )
    ''')

    # NOVA Tabela 5: Preferências de itens por usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_item_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            is_enabled BOOLEAN NOT NULL DEFAULT 1, -- 1 para true, 0 para false
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES itens_relevantes (id) ON DELETE CASCADE,
            UNIQUE(user_id, item_id)
        )
    ''')

    # Garante que o usuário admin padrão exista com a permissão correta
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        adicionar_usuario('admin', 'admin', role='admin')
    
    # Adiciona o usuário padrão 'mdr' se ele não existir
    cursor.execute("SELECT * FROM users WHERE username = 'mdr'")
    if not cursor.fetchone():
        adicionar_usuario("mdr", "mdr.123")


    conn.commit()
    conn.close()
    print("✔️ Banco de dados (re)inicializado com a estrutura de permissões.")

# --- Funções de Usuários e Permissões (Atualizadas) ---

def adicionar_usuario(username, password, role='user'):
    """Adiciona um novo usuário ao banco com senha criptografada e uma permissão (role)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, role))
        conn.commit()
        print(f"✔️ Usuário '{username}' com permissão '{role}' criado com sucesso.")
    except sqlite3.IntegrityError:
        # Se o usuário já existe, podemos garantir que a permissão de admin seja atualizada
        if role == 'admin':
            cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
            conn.commit()
            print(f"✔️ Permissão do usuário '{username}' atualizada para 'admin'.")
        else:
            print(f"⚠️ Usuário '{username}' já existe.")
    finally:
        conn.close()

def buscar_usuario_por_nome(username):
    """Busca um usuário pelo nome e retorna seus dados, incluindo a 'role'."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

# --- Funções de Processos e Subsídios (Sua lógica original mantida) ---

def adicionar_processos_para_monitorar(processos_com_dados: list):
    """Adiciona uma lista de processos ou atualiza dados se já existir."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()

    for processo_info in processos_com_dados:
        numero_limpo = _limpar_numero(processo_info['numero'])
        cursor.execute(
            """
            INSERT INTO processos (numero_processo, responsavel_principal, classificacao, status_geral, data_ultima_atualizacao)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(numero_processo) DO UPDATE SET
                responsavel_principal = excluded.responsavel_principal,
                classificacao = excluded.classificacao;
            """,
            (numero_limpo, processo_info['responsavel'], processo_info['classificacao'], 'Em Monitoramento', agora)
        )
    conn.commit()
    conn.close()
    print(f"✔️ {len(processos_com_dados)} processos adicionados/atualizados para monitoramento.")


def atualizar_status_processo(numero_processo: str, lista_subsidios: list):
    """
    Atualiza o status de um processo com base nos subsídios e na lista de itens relevantes.
    Esta é a versão unificada e corrigida.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_processo_limpo = _limpar_numero(numero_processo)

    # 1. Salva todos os subsídios encontrados
    for subsidio in lista_subsidios:
        cursor.execute(
            """
            INSERT INTO subsidios_atuais (numero_processo, item, status, data_atualizacao)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(numero_processo, item) DO UPDATE SET
                status = excluded.status,
                data_atualizacao = excluded.data_atualizacao;
            """,
            (numero_processo_limpo, subsidio['item'], subsidio['status'], agora)
        )
    
    # 2. Busca a lista mestre de itens relevantes
    cursor.execute("SELECT item_nome FROM itens_relevantes")
    itens_relevantes_set = {row[0] for row in cursor.fetchall()}
    print(f"   - Itens relevantes para verificação: {itens_relevantes_set}")

    def is_concluido(status_str):
        status_lower = status_str.lower()
        return status_lower == 'concluído' or status_lower == 'concluido'

    # 3. Lógica de atualização de status
    status_geral_novo = 'Em Monitoramento'
    if itens_relevantes_set:
        subsidios_concluidos_encontrados = {s['item'] for s in lista_subsidios if is_concluido(s['status'])}
        
        # Verifica se o conjunto de itens relevantes é um subconjunto dos concluídos
        if itens_relevantes_set.issubset(subsidios_concluidos_encontrados):
            print(f"   - Todos os {len(itens_relevantes_set)} subsídios relevantes estão concluídos. Marcando como pendente.")
            status_geral_novo = 'Pendente Ciencia'

    # 4. Atualiza o status do processo
    cursor.execute(
        "UPDATE processos SET status_geral = ?, data_ultima_atualizacao = ? WHERE numero_processo = ?",
        (status_geral_novo, agora, numero_processo_limpo)
    )
    
    conn.commit()
    conn.close()
    print(f"✔️ Status do processo {numero_processo_limpo} atualizado para: {status_geral_novo}")


def marcar_como_arquivado(numero_processo: str):
    """Muda o status de um processo para 'Arquivado'."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_processo_limpo = _limpar_numero(numero_processo)
    cursor.execute(
        "UPDATE processos SET status_geral = ?, data_ultima_atualizacao = ? WHERE numero_processo = ?",
        ('Arquivado', agora, numero_processo_limpo)
    )
    conn.commit()
    conn.close()
    print(f"✔️ Processo {numero_processo_limpo} movido para o histórico (Arquivado).")

def buscar_painel_dados():
    """Busca os processos ativos e seus subsídios para o painel."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, numero_processo, responsavel_principal, classificacao, status_geral, data_ultima_atualizacao FROM processos WHERE status_geral != 'Arquivado' ORDER BY data_ultima_atualizacao DESC"
    )
    dados_painel = [dict(row) for row in cursor.fetchall()]
    
    for processo in dados_painel:
        cursor.execute(
            "SELECT item, status FROM subsidios_atuais WHERE numero_processo = ? ORDER BY id",
            (processo['numero_processo'],)
        )
        processo['subsidios'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return dados_painel

def buscar_processos_em_monitoramento() -> list:
    """Retorna a lista de números de processos 'Em Monitoramento'."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT numero_processo FROM processos WHERE status_geral = 'Em Monitoramento'")
    processos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return processos

def buscar_historico_arquivado():
    """Busca todos os processos com status 'Arquivado'."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, numero_processo, responsavel_principal, classificacao, data_ultima_atualizacao FROM processos WHERE status_geral = 'Arquivado' ORDER BY data_ultima_atualizacao DESC"
    )
    historico = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return historico

# --- Funções de Itens Relevantes (Sua lógica, mas adaptada para o modelo Admin) ---

def buscar_itens_relevantes():
    """Busca a lista de todos os itens relevantes (agora gerenciada pelo admin)."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_nome FROM itens_relevantes ORDER BY item_nome")
    itens = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return itens

def salvar_itens_relevantes(itens: list):
    """Apaga a lista antiga e salva a nova lista de itens relevantes (ação de admin)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM itens_relevantes")
        if itens:
            itens_tuplas = [(item.strip(),) for item in itens if item.strip()]
            cursor.executemany("INSERT INTO itens_relevantes (item_nome) VALUES (?)", itens_tuplas)
        conn.commit()
        print(f"✔️ Lista de itens relevantes salva com {len(itens)} itens.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao salvar itens relevantes: {e}")
    finally:
        conn.close()

# --- NOVAS Funções para Preferências de Itens (Usuário) ---

def get_itens_com_preferencias_usuario(user_id: int):
    """Retorna a lista de itens com as preferências de um usuário específico."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Garante que o usuário tenha uma entrada de preferência para todos os itens existentes
    cursor.execute('''
        INSERT OR IGNORE INTO user_item_preferences (user_id, item_id)
        SELECT ?, id FROM itens_relevantes
        WHERE id NOT IN (SELECT item_id FROM user_item_preferences WHERE user_id = ?)
    ''', (user_id, user_id))
    conn.commit()

    # Busca todos os itens, juntando com a preferência do usuário
    cursor.execute('''
        SELECT ir.id, ir.item_nome, uip.is_enabled
        FROM itens_relevantes ir
        JOIN user_item_preferences uip ON ir.id = uip.item_id
        WHERE uip.user_id = ?
    ''', (user_id,))
    
    itens = [{'id': row[0], 'item_nome': row[1], 'is_enabled': bool(row[2])} for row in cursor.fetchall()]
    conn.close()
    return itens

def atualizar_preferencia_usuario(user_id: int, item_id: int, is_enabled: bool):
    """Atualiza a preferência (habilitar/desabilitar) de um usuário para um item."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_item_preferences
        SET is_enabled = ?
        WHERE user_id = ? AND item_id = ?
    ''', (1 if is_enabled else 0, user_id, item_id))
    conn.commit()
    conn.close()


# --- Bloco de Execução Principal ---
if __name__ == '__main__':
    # Executa a inicialização para garantir que o schema esteja atualizado
    inicializar_banco()