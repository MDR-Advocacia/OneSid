import sqlite3
import datetime
import re

DB_NAME = 'rpa_dados.db'

def _limpar_numero(numero_processo_bruto: str) -> str:
    """Remove todos os caracteres não numéricos de uma string de número de processo."""
    return re.sub(r'\D', '', numero_processo_bruto)

def inicializar_banco():
    """Cria ou atualiza as tabelas do banco de dados para o novo modelo."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT UNIQUE,
            status_geral TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_ultima_atualizacao TIMESTAMP
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
    conn.commit()
    conn.close()
    print("✔️ Banco de dados (re)inicializado com a estrutura de estado atual.")

def adicionar_processos_para_monitorar(numeros_processo: list):
    """Adiciona novos processos à tabela de monitoramento, sempre no formato limpo."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    for numero in numeros_processo:
        numero_limpo = _limpar_numero(numero)
        cursor.execute(
            "INSERT OR IGNORE INTO processos (numero_processo, status_geral, data_ultima_atualizacao) VALUES (?, ?, ?)",
            (numero_limpo, 'Em Monitoramento', agora)
        )
    conn.commit()
    conn.close()
    print(f"✔️ Processos adicionados/verificados na tabela de monitoramento.")

def atualizar_status_processo(numero_processo: str, lista_subsidios: list):
    """Atualiza o status de um processo e o estado atual de seus subsídios."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.datetime.now()
    numero_processo_limpo = _limpar_numero(numero_processo)
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
    todos_concluidos = all(is_concluido(s['status']) for s in lista_subsidios)
    status_geral_novo = 'Pendente Ciencia' if todos_concluidos else 'Em Monitoramento'
    cursor.execute(
        "UPDATE processos SET status_geral = ?, data_ultima_atualizacao = ? WHERE numero_processo = ?",
        (status_geral_novo, agora, numero_processo_limpo)
    )
    conn.commit()
    conn.close()
    print(f"✔️ Status do processo {numero_processo_limpo} e de seus subsídios atualizado para: {status_geral_novo}")

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
    """Busca os processos ativos e os detalhes dos seus subsídios atuais."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, numero_processo, status_geral, data_ultima_atualizacao FROM processos WHERE status_geral != 'Arquivado' ORDER BY data_ultima_atualizacao DESC"
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
    """Busca todos os processos arquivados para a tela de histórico."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, numero_processo, status_geral, data_ultima_atualizacao FROM processos WHERE status_geral = 'Arquivado' ORDER BY data_ultima_atualizacao DESC"
    )
    historico = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return historico