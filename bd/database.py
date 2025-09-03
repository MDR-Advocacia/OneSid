import sqlite3
import datetime
import re

DB_NAME = 'rpa_dados.db'

def _limpar_numero(numero_processo_bruto: str) -> str:
    """Remove todos os caracteres não numéricos de uma string."""
    return re.sub(r'\D', '', numero_processo_bruto)

def inicializar_banco():
    """Cria ou atualiza as tabelas do banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_relevantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_nome TEXT UNIQUE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✔️ Banco de dados (re)inicializado com a estrutura mais recente.")

def adicionar_processos_para_monitorar(processos_com_dados: list):
    """Adiciona uma lista de processos ou atualiza o responsável/classificação se já existir."""
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
    Atualiza o status de um processo com base nos subsídios RELEVANTES
    e salva o log de todos os subsídios encontrados.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_processo_limpo = _limpar_numero(numero_processo)

    cursor.execute("SELECT item_nome FROM itens_relevantes")
    itens_relevantes_set = {row[0] for row in cursor.fetchall()}
    print(f"   - Itens relevantes para verificação: {itens_relevantes_set}")

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
    
    def is_concluido(status_str):
        status_lower = status_str.lower()
        return status_lower == 'concluído' or status_lower == 'concluido'

    # --- LÓGICA CORRIGIDA ---
    status_geral_novo = 'Em Monitoramento'

    # Só prossiga se houver uma lista de itens relevantes definida
    if itens_relevantes_set:
        # Pega todos os subsídios encontrados para o processo que são concluídos
        subsidios_concluidos_encontrados = {s['item'] for s in lista_subsidios if is_concluido(s['status'])}
        
        # Verifica se a lista de itens relevantes é um SUBCONJUNTO da lista de concluídos.
        # Ou seja, verifica se TODOS os itens relevantes estão presentes na lista de concluídos.
        if itens_relevantes_set.issubset(subsidios_concluidos_encontrados):
            print(f"   - Todos os {len(itens_relevantes_set)} subsídios relevantes estão concluídos. Marcando como pendente.")
            status_geral_novo = 'Pendente Ciencia'
    # --- FIM DA LÓGICA CORRIGIDA ---

    cursor.execute(
        "UPDATE processos SET status_geral = ?, data_ultima_atualizacao = ? WHERE numero_processo = ?",
        (status_geral_novo, agora, numero_processo_limpo)
    )
    
    conn.commit()
    conn.close()
    print(f"✔️ Status do processo {numero_processo_limpo} atualizado para: {status_geral_novo}")
    """
    Atualiza o status de um processo com base nos subsídios RELEVANTES
    e salva o log de todos os subsídios encontrados.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_processo_limpo = _limpar_numero(numero_processo)

    cursor.execute("SELECT item_nome FROM itens_relevantes")
    itens_relevantes = {row[0] for row in cursor.fetchall()}
    print(f"   - Itens relevantes para verificação: {itens_relevantes}")

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
    
    def is_concluido(status_str):
        status_lower = status_str.lower()
        return status_lower == 'concluído' or status_lower == 'concluido'

    subsidios_relevantes_encontrados = [s for s in lista_subsidios if s['item'] in itens_relevantes]
    
    status_geral_novo = 'Em Monitoramento'
    
    # Se a lista de itens relevantes foi definida e TODOS os itens relevantes encontrados estão concluídos
    if itens_relevantes and subsidios_relevantes_encontrados and all(is_concluido(s['status']) for s in subsidios_relevantes_encontrados):
        print(f"   - Todos os {len(subsidios_relevantes_encontrados)} subsídios relevantes estão concluídos. Marcando como pendente.")
        status_geral_novo = 'Pendente Ciencia'
    
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
    """
    Busca os processos ativos, incluindo o responsável e classificação, e os detalhes dos subsídios.
    """
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
        subsidios_detalhes = [dict(row) for row in cursor.fetchall()]
        processo['subsidios'] = subsidios_detalhes
    
    conn.close()
    return dados_painel

def buscar_processos_em_monitoramento() -> list:
    """Busca e retorna uma lista com os números dos processos que estão 'Em Monitoramento'."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT numero_processo FROM processos WHERE status_geral = 'Em Monitoramento'"
    )
    processos = [row['numero_processo'] for row in cursor.fetchall()]
    conn.close()
    return processos

def buscar_historico_arquivado():
    """
    Busca todos os processos arquivados, incluindo o responsável e classificação.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, numero_processo, responsavel_principal, classificacao, data_ultima_atualizacao FROM processos WHERE status_geral = 'Arquivado' ORDER BY data_ultima_atualizacao DESC"
    )
    historico = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return historico

def buscar_itens_relevantes():
    """Busca a lista de todos os itens relevantes."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_nome FROM itens_relevantes ORDER BY item_nome")
    itens = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return itens

def salvar_itens_relevantes(itens: list):
    """Apaga a lista antiga e salva a nova lista de itens relevantes."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM itens_relevantes")
        
        for item in itens:
            if item.strip():
                cursor.execute("INSERT INTO itens_relevantes (item_nome) VALUES (?)", (item.strip(),))
        
        conn.commit()
        print(f"✔️ Lista de itens relevantes salva com {len(itens)} itens.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao salvar itens relevantes: {e}")
    finally:
        conn.close()