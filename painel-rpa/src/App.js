import React, { useState, useEffect } from 'react';
import './App.css';

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
    const numbers = processInput.split('\n').filter(num => num.trim() !== '');
    if (numbers.length === 0) {
        setMessage('Por favor, insira ao menos um processo.');
        return;
    };

    setIsLoading(true);
    setMessage('Adicionando e consultando novos processos...');
    
    try {
      const response = await fetch(`${API_BASE_URL}/add-and-run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ processos: numbers }),
      });
      if (!response.ok) throw new Error('Falha ao submeter novos processos.');
      
      const updatedPanelData = await response.json();
      setPanelList(updatedPanelData);
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

        const updatedPanelData = await response.json();
        setPanelList(updatedPanelData);
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

  return (
    <>
      <Modal processo={modalProcess} onClose={() => setModalProcess(null)} />
      <div className="App">
        <header className="App-header">
          <h1>Painel de Monitoramento de Subsídios</h1>
        </header>
        <main className="panel-container">
          <div className="input-section">
            <h2>Submeter Novos Processos</h2>
            <textarea
              rows="8"
              placeholder="Cole os números dos processos aqui..."
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
            {panelList.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Número do Processo</th>
                    <th>Status</th>
                    <th>Última Verificação</th>
                    <th>Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {panelList.map((proc) => (
                    <tr key={proc.id}>
                      <td>{proc.id}</td>
                      <td>
                        <a href="#" onClick={(e) => { e.preventDefault(); setModalProcess(proc); }}>
                          {proc.numero_processo}
                        </a>
                      </td>
                      <td>
                        <span className={`status status-${proc.status_geral.replace(/\s+/g, '-')}`}>
                          {proc.status_geral}
                        </span>
                      </td>
                      <td>{new Date(proc.data_ultima_atualizacao).toLocaleString('pt-BR')}</td>
                      <td>
                        {proc.status_geral === 'Pendente Ciencia' && (
                          <button className="archive-button" onClick={() => handleArchiveProcess(proc.numero_processo)}>
                            Dar Ciência
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p>Nenhum processo em monitoramento ou pendente.</p>}
          </div>

          <div className="results-section">
            <h2>Histórico de Processos Arquivados</h2>
            {historyList.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Número do Processo</th>
                    <th>Data de Arquivamento</th>
                  </tr>
                </thead>
                <tbody>
                  {historyList.map((proc) => (
                    <tr key={proc.id}>
                      <td>{proc.id}</td>
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