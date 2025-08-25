import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = 'http://127.0.0.1:5000';

// Componente para o Modal
const Modal = ({ processo, onClose }) => {
    if (!processo) return null;

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h3>Detalhes do Subsídio - Processo {processo.numero_processo}</h3>
                {processo.subsidios && processo.subsidios.length > 0 ? (
                    <table>
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {processo.subsidios.map((sub, index) => (
                                <tr key={index}>
                                    <td>{sub.item}</td>
                                    <td><strong>{sub.status}</strong></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p>Nenhum detalhe de subsídio encontrado para esta consulta.</p>
                )}
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
  const [modalProcess, setModalProcess] = useState(null); // Estado para controlar o modal

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

  const handleSubmitProcesses = async () => {
    const numbers = processInput.split('\n').filter(num => num.trim() !== '');
    if (numbers.length === 0) return;

    setIsLoading(true);
    setMessage('Enviando processos e executando RPA...');
    
    try {
      const response = await fetch(`${API_BASE_URL}/submit-processos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ processos: numbers }),
      });
      if (!response.ok) throw new Error('Falha ao submeter processos.');
      
      await fetchData();
      setMessage('RPA executado e painel atualizado com sucesso!');
      setProcessInput('');

    } catch (error) {
      console.error("Erro no RPA:", error);
      setMessage('Erro durante a execução do RPA.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleArchiveProcess = async (numero_processo) => {
    // ... (função sem alterações)
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
              placeholder="Cole os números dos processos aqui, um por linha..."
              value={processInput}
              onChange={(e) => setProcessInput(e.target.value)}
              disabled={isLoading}
            />
            <button onClick={handleSubmitProcesses} disabled={isLoading}>
              {isLoading ? 'Executando RPA...' : 'Adicionar e Consultar'}
            </button>
            {message && <p className="feedback-message">{message}</p>}
          </div>
          
          <div className="results-section">
            <h2>Painel de Controle</h2>
            {panelList.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th>Número do Processo</th>
                    <th>Status</th>
                    <th>Última Verificação</th>
                    <th>Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {panelList.map((proc) => (
                    <tr key={proc.numero_processo}>
                      <td>
                        {/* AQUI ESTÁ O HYPERLINK */}
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
            {/* ... (seção de histórico sem alterações) ... */}
          </div>
        </main>
      </div>
    </>
  );
}

export default App;