import React, { useState, useEffect, useMemo } from 'react';
import './App.css';
import logo from './assets/logo-onesid.png';

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

const ItensRelevantesModal = ({ onClose }) => {
    // Estado para a lista de itens
    const [itens, setItens] = useState([]);
    // Estado para o novo item que será adicionado
    const [novoItem, setNovoItem] = useState('');
    // Estado para as mensagens de feedback (Carregando, Salvo, Erro)
    const [status, setStatus] = useState('Carregando...');

    // Efeito para buscar os itens quando o modal abre
    useEffect(() => {
        const fetchItens = async () => {
            try {
                setStatus('Carregando...');
                const response = await fetch(`${API_BASE_URL}/itens-relevantes`);
                const data = await response.json();
                if (Array.isArray(data)) {
                    setItens(data.map(item => item.item_nome));
                }
                setStatus('');
            } catch (e) {
                setStatus('Erro ao carregar itens.');
            }
        };
        fetchItens();
    }, []);

    // Função para adicionar um novo item à lista (no estado)
    const handleAddItem = () => {
        if (novoItem && !itens.includes(novoItem.trim())) {
            setItens([...itens, novoItem.trim()]);
            setNovoItem(''); // Limpa o input
        }
    };

    // Função para remover um item da lista (no estado)
    const handleRemoveItem = (itemToRemove) => {
        setItens(itens.filter(item => item !== itemToRemove));
    };

    // Função para salvar a lista final no banco de dados
    const handleSave = async () => {
        try {
            setStatus('Salvando...');
            await fetch(`${API_BASE_URL}/itens-relevantes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ itens: itens }),
            });
            setStatus('Salvo com sucesso!');
            setTimeout(onClose, 1000);
        } catch (e) {
            setStatus('Erro ao salvar.');
        }
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h3>Definir Itens Relevantes para Monitoramento</h3>
                <p>Adicione ou remova os itens que devem ser considerados para mover um processo para "Pendente Ciência".</p>
                
                <div className="item-manager">
                    <div className="item-add-form">
                        <input
                            type="text"
                            value={novoItem}
                            onChange={(e) => setNovoItem(e.target.value)}
                            placeholder="Digite o nome do novo item..."
                            onKeyPress={(e) => e.key === 'Enter' && handleAddItem()}
                        />
                        <button onClick={handleAddItem} className="add-button">Adicionar</button>
                    </div>
                    
                    <ul className="item-list">
                        {itens.length > 0 ? itens.map((item, index) => (
                            <li key={index}>
                                <span>{item}</span>
                                <button onClick={() => handleRemoveItem(item)} className="remove-button">Remover</button>
                            </li>
                        )) : <p>Nenhum item relevante definido.</p>}
                    </ul>
                </div>

                <div className="modal-actions">
                    <span className="feedback-message">{status}</span>
                    <button onClick={handleSave} className="primary-button">Salvar e Fechar</button>
                    <button onClick={onClose} className="secondary-button">Cancelar</button>
                </div>
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
    numero_processo: '',
    classificacao: ''
  });
  const [sortConfig, setSortConfig] = useState({ key: 'id', direction: 'descending' });
  const [showItensModal, setShowItensModal] = useState(false);

  const fetchData = async () => {
    try {
      const panelResponse = await fetch(`${API_BASE_URL}/painel`);
      const panelData = await panelResponse.json();
      // Verificação de segurança para garantir que sempre teremos um array
      setPanelList(Array.isArray(panelData) ? panelData : []);

      const historyResponse = await fetch(`${API_BASE_URL}/historico`);
      const historyData = await historyResponse.json();
      // Verificação de segurança para garantir que sempre teremos um array
      setHistoryList(Array.isArray(historyData) ? historyData : []);
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
        if (parts.length >= 4) {
            return { 
                responsavel: parts[1].trim(), 
                numero: parts[2].trim(),
                classificacao: parts[3].trim()
            };
        }
        return null;
    }).filter(Boolean);

    if (processosParaEnviar.length === 0) {
        setMessage('Nenhum processo válido encontrado. Verifique o formato colado da planilha.');
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
        const classificacaoMatch = proc.classificacao?.toLowerCase().includes(filters.classificacao.toLowerCase()) ?? true;
        return responsavelMatch && processoMatch && classificacaoMatch;
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
      {showItensModal && <ItensRelevantesModal onClose={() => setShowItensModal(false)} />}
      <Modal processo={modalProcess} onClose={() => setModalProcess(null)} />
      <div className="App">
        <header className="App-header">
          <img src={logo} className="header-logo" alt="Logo OneSid" />
          <h1>OneSid</h1>
          <button className="header-button" onClick={() => setShowItensModal(true)}>
            Definir Itens
          </button>
        </header>
        <main className="panel-container">
          <div className="input-section">
            <h2>Submeter Novos Processos</h2>
            <p>Copie e cole da sua planilha (as 4 colunas).</p>
            <textarea
              rows="8"
              placeholder="Escritório [TAB] Responsável [TAB] Processo [TAB] Classificação"
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
              <input type="text" name="numero_processo" placeholder="Filtrar por Número..." value={filters.numero_processo} onChange={handleFilterChange} className="filter-input" />
              <input type="text" name="classificacao" placeholder="Filtrar por Classificação..." value={filters.classificacao} onChange={handleFilterChange} className="filter-input" />
            </div>
            {sortedAndFilteredPanelList.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th onClick={() => requestSort('id')} className="sortable-header">ID{getSortIcon('id')}</th>
                    <th>Responsável Principal</th>
                    <th>Número do Processo</th>
                    <th>Classificação dos Subsídios</th>
                    <th onClick={() => requestSort('status_geral')} className="sortable-header">Status{getSortIcon('status_geral')}</th>
                    <th onClick={() => requestSort('data_ultima_atualizacao')} className="sortable-header">Última Verificação{getSortIcon('data_ultima_atualizacao')}</th>
                    <th>Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedAndFilteredPanelList.map((proc) => (
                    <tr key={proc.id}>
                      <td>{proc.id}</td>
                      <td>{proc.responsavel_principal}</td>
                      <td><button className="link-button" onClick={() => setModalProcess(proc)}>{proc.numero_processo}</button></td>
                      <td>{proc.classificacao}</td>
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
                <thead><tr><th>ID</th><th>Responsável Principal</th><th>Número do Processo</th><th>Classificação dos Subsídios</th><th>Data de Arquivamento</th></tr></thead>
                <tbody>
                  {historyList.map((proc) => (
                    <tr key={proc.id}>
                      <td>{proc.id}</td>
                      <td>{proc.responsavel_principal}</td>
                      <td>{proc.numero_processo}</td>
                      <td>{proc.classificacao}</td>
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