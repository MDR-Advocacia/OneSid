import sqlite3
import datetime

DB_NAME = 'rpa_dados.db'

def inicializar_banco():
    """
    Cria ou atualiza as tabelas do banco de dados para o novo modelo.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT UNIQUE,
            status_geral TEXT, -- 'Em Monitoramento', 'Pendente Ciencia', 'Arquivado'
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_ultima_atualizacao TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subsidios_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT,
            item TEXT,
            status TEXT,
            data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✔️ Banco de dados (re)inicializado com a nova estrutura.")

def adicionar_processos_para_monitorar(numeros_processo: list):
    """
    Adiciona novos processos à tabela de monitoramento.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    
    for numero in numeros_processo:
        cursor.execute(
            "INSERT OR IGNORE INTO processos (numero_processo, status_geral, data_ultima_atualizacao) VALUES (?, ?, ?)",
            (numero, 'Em Monitoramento', agora)
        )
    
    conn.commit()
    conn.close()
    print(f"✔️ Processos adicionados/verificados na tabela de monitoramento.")

def atualizar_status_processo(numero_processo: str, lista_subsidios: list):
    """
    Atualiza o status de um processo e salva o log detalhado.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()

    for subsidio in lista_subsidios:
        cursor.execute(
            "INSERT INTO subsidios_log (numero_processo, item, status, data_consulta) VALUES (?, ?, ?, ?)",
            (numero_processo, subsidio['item'], subsidio['status'], agora)
        )

    def is_concluido(status_str):
        status_lower = status_str.lower()
        return status_lower == 'concluído' or status_lower == 'concluido'

    todos_concluidos = all(is_concluido(s['status']) for s in lista_subsidios)
    status_geral_novo = 'Pendente Ciencia' if todos_concluidos else 'Em Monitoramento'

    cursor.execute(
        "UPDATE processos SET status_geral = ?, data_ultima_atualizacao = ? WHERE numero_processo = ?",
        (status_geral_novo, agora, numero_processo)
    )
    
    conn.commit()
    conn.close()
    print(f"✔️ Status do processo {numero_processo} atualizado para: {status_geral_novo}")

def marcar_como_arquivado(numero_processo: str):
    """
    Muda o status de um processo para 'Arquivado'.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    
    cursor.execute(
        "UPDATE processos SET status_geral = ?, data_ultima_atualizacao = ? WHERE numero_processo = ?",
        ('Arquivado', agora, numero_processo)
    )
    
    conn.commit()
    conn.close()
    print(f"✔️ Processo {numero_processo} movido para o histórico (Arquivado).")

# --- FUNÇÃO ATUALIZADA PARA INCLUIR DETALHES DOS SUBSÍDIOS ---
def buscar_painel_dados():
    """
    Busca os processos ativos e os detalhes dos seus subsídios mais recentes.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Busca os processos que não estão arquivados
    cursor.execute(
        "SELECT numero_processo, status_geral, data_ultima_atualizacao FROM processos WHERE status_geral != 'Arquivado' ORDER BY data_ultima_atualizacao DESC"
    )
    dados_painel = [dict(row) for row in cursor.fetchall()]
    
    # 2. Para cada processo, busca os logs de subsídios da última consulta
    for processo in dados_painel:
        cursor.execute(
            """
            SELECT item, status FROM subsidios_log 
            WHERE numero_processo = ? AND DATE(data_consulta) = DATE(?)
            ORDER BY id
            """,
            (processo['numero_processo'], processo['data_ultima_atualizacao'])
        )
        subsidios_detalhes = [dict(row) for row in cursor.fetchall()]
        processo['subsidios'] = subsidios_detalhes # Adiciona a lista ao objeto do processo
    
    conn.close()
    return dados_painel

def buscar_historico_arquivado():
    """
    Busca todos os processos arquivados para a tela de histórico.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT numero_processo, status_geral, data_ultima_atualizacao FROM processos WHERE status_geral = 'Arquivado' ORDER BY data_ultima_atualizacao DESC"
    )
    historico = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return historico