import React, { useState, useEffect, useMemo } from 'react';
import './App.css';
import logo from './assets/logo-onesid.png'; // Importa a imagem do logo

const API_BASE_URL = 'http://127.0.0.1:5000';

const Modal = ({ processo, onClose }) => {
    if (!processo) return null;
    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h3>Detalhes do Subsídio - Processo {processo.numero_processo}</h3>
                {processo.subsidios && processo.subsidios.length > 0 ? (
                    <table>
                        <thead><tr><th>Item</th><th>Status</th></tr></thead>
                        <tbody>
                            {processo.subsidios.map((sub, index) => (
                                <tr key={index}>
                                    <td>{sub.item}</td>
                                    <td><strong>{sub.status}</strong></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : <p>Nenhum detalhe de subsídio encontrado para esta consulta.</p>}
                <button className="modal-close-button" onClick={onClose}>Fechar</button>
            </div>
        </div>
    );
};

function App() {
  const [processInput, setProcessInput] = useState('');
  const [panelList, setPanelList] = useState([]);
  const [historyList, setHistoryList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [modalProcess, setModalProcess] = useState(null);
  const [filters, setFilters] = useState({
    responsavel: '',
    numero_processo: ''
  });
  const [sortConfig, setSortConfig] = useState({ key: 'id', direction: 'descending' });

  const fetchData = async () => {
    try {
      const panelResponse = await fetch(`${API_BASE_URL}/painel`);
      const panelData = await panelResponse.json();
      setPanelList(panelData);
      const historyResponse = await fetch(`${API_BASE_URL}/historico`);
      const historyData = await historyResponse.json();
      setHistoryList(historyData);
    } catch (error) {
      console.error("Falha ao buscar dados:", error);
      setMessage('Erro de conexão com o servidor.');
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAddAndRun = async () => {
    const lines = processInput.split('\n').filter(line => line.trim() !== '');
    if (lines.length === 0) {
        setMessage('Por favor, insira os dados no formato correto.');
        return;
    }
    const processosParaEnviar = lines.map(line => {
        const parts = line.split('\t');
        if (parts.length >= 2) {
            return { responsavel: parts[0].trim(), numero: parts[1].trim() };
        }
        return null;
    }).filter(Boolean);
    if (processosParaEnviar.length === 0) {
        setMessage('Nenhum processo válido. Use o formato: Responsável [TAB] Processo.');
        return;
    }
    setIsLoading(true);
    setMessage('Adicionando e consultando novos processos...');
    try {
      const response = await fetch(`${API_BASE_URL}/add-and-run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ processos: processosParaEnviar }),
      });
      if (!response.ok) throw new Error('Falha ao submeter novos processos.');
      await fetchData();
      setMessage('Novos processos consultados com sucesso!');
      setProcessInput('');
    } catch (error) {
      setMessage('Erro ao consultar novos processos.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunMonitoring = async () => {
    setIsLoading(true);
    setMessage('Iniciando monitoramento dos processos pendentes...');
    try {
        const response = await fetch(`${API_BASE_URL}/run-monitoring`, { method: 'POST' });
        if (!response.ok) throw new Error('Falha ao rodar monitoramento.');
        await fetchData();
        setMessage('Monitoramento finalizado com sucesso!');
    } catch (error) {
        setMessage('Erro durante o monitoramento.');
    } finally {
        setIsLoading(false);
    }
  };

  const handleArchiveProcess = async (numero_processo) => {
    try {
        setMessage(`Arquivando processo ${numero_processo}...`);
        const response = await fetch(`${API_BASE_URL}/arquivar-processo`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ numero_processo: numero_processo }),
        });
        if (!response.ok) throw new Error('Falha ao arquivar processo.');
        await fetchData();
        setMessage(`Processo ${numero_processo} arquivado com sucesso!`);
    } catch (error) {
        console.error("Erro ao arquivar:", error);
        setMessage('Erro ao arquivar o processo.');
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prevFilters => ({
      ...prevFilters,
      [name]: value
    }));
  };

  const sortedAndFilteredPanelList = useMemo(() => {
    let list = [...panelList];
    list = list.filter(proc => {
        const responsavelMatch = proc.responsavel_principal?.toLowerCase().includes(filters.responsavel.toLowerCase()) ?? true;
        const processoMatch = proc.numero_processo.toLowerCase().includes(filters.numero_processo.toLowerCase());
        return responsavelMatch && processoMatch;
    });
    if (sortConfig.key !== null) {
      list.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return list;
  }, [panelList, filters, sortConfig]);

  const requestSort = (key) => {
    let direction = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const getSortIcon = (name) => {
    if (sortConfig.key !== name) return null;
    return sortConfig.direction === 'ascending' ? ' ▲' : ' ▼';
  };

  return (
    <>
      <Modal processo={modalProcess} onClose={() => setModalProcess(null)} />
      <div className="App">
        <header className="App-header">
          <img src={logo} className="header-logo" alt="Logo OneSid" />
          <h3>OneSid - RPA para acompanhamento de subsídios</h3>
        </header>
        <main className="panel-container">
          <div className="input-section">
            <h2>Submeter Novos Processos</h2>
            <p>Copie e cole da sua planilha (Responsável [TAB] Processo).</p>
            <textarea
              rows="8"
              placeholder="Arthur Augusto Alves de Almeida	6031308-17.2025.8.03.0001"
              value={processInput}
              onChange={(e) => setProcessInput(e.target.value)}
              disabled={isLoading}
            />
            <div className="button-group">
                <button onClick={handleAddAndRun} disabled={isLoading}>
                    {isLoading ? 'Aguarde...' : 'Adicionar e Consultar Novos'}
                </button>
                <button onClick={handleRunMonitoring} disabled={isLoading} className="secondary-button">
                    {isLoading ? 'Aguarde...' : "Rodar Monitoramento"}
                </button>
            </div>
            {message && <p className="feedback-message">{message}</p>}
          </div>
          <div className="results-section">
            <h2>Painel de Controle</h2>
            <div className="filter-container">
              <input type="text" name="responsavel" placeholder="Filtrar por Responsável..." value={filters.responsavel} onChange={handleFilterChange} className="filter-input" />
              <input type="text" name="numero_processo" placeholder="Filtrar por Número do Processo..." value={filters.numero_processo} onChange={handleFilterChange} className="filter-input" />
            </div>
            {sortedAndFilteredPanelList.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th onClick={() => requestSort('id')} className="sortable-header">ID{getSortIcon('id')}</th>
                    <th>Responsável Principal</th>
                    <th>Número do Processo</th>
                    <th>Status</th>
                    <th onClick={() => requestSort('data_ultima_atualizacao')} className="sortable-header">Última Verificação{getSortIcon('data_ultima_atualizacao')}</th>
                    <th>Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedAndFilteredPanelList.map((proc) => (
                    <tr key={proc.id}>
                      <td>{proc.id}</td>
                      <td>{proc.responsavel_principal}</td>
                      <td>
                        <button className="link-button" onClick={() => setModalProcess(proc)}>
                          {proc.numero_processo}
                        </button>
                      </td>
                      <td><span className={`status status-${proc.status_geral.replace(/\s+/g, '-')}`}>{proc.status_geral}</span></td>
                      <td>{new Date(proc.data_ultima_atualizacao).toLocaleString('pt-BR')}</td>
                      <td>{proc.status_geral === 'Pendente Ciencia' && (<button className="archive-button" onClick={() => handleArchiveProcess(proc.numero_processo)}>Dar Ciência</button>)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p>Nenhum processo encontrado com os filtros aplicados.</p>}
          </div>
          <div className="results-section">
            <h2>Histórico de Processos Arquivados</h2>
            {historyList.length > 0 ? (
              <table>
                <thead><tr><th>ID</th><th>Responsável Principal</th><th>Número do Processo</th><th>Data de Arquivamento</th></tr></thead>
                <tbody>
                  {historyList.map((proc) => (
                    <tr key={proc.id}>
                      <td>{proc.id}</td>
                      <td>{proc.responsavel_principal}</td>
                      <td>{proc.numero_processo}</td>
                      <td>{new Date(proc.data_ultima_atualizacao).toLocaleString('pt-BR')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p>Nenhum processo no histórico.</p>}
          </div>
        </main>
      </div>
    </>
  );
}

export default App;