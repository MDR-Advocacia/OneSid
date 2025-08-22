import React, { useState } from 'react';
import './App.css';

const API_URL = 'http://127.0.0.1:5000/run-rpa';

function App() {
  const [processInput, setProcessInput] = useState('');
  const [processList, setProcessList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleStartRPA = async () => {
    const numbers = processInput.split('\n').filter(num => num.trim() !== '');
    if (numbers.length === 0) {
      alert("Por favor, insira pelo menos um número de processo.");
      return;
    }

    const initialList = numbers.map(number => ({
      number: number.trim(),
      status: 'Enviando para o RPA...',
      subsidios: []
    }));
    
    setProcessList(initialList);
    setIsLoading(true);

    console.log("Iniciando requisição para a API em:", API_URL);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ processos: numbers }),
      });

      console.log("Resposta da API recebida. Status:", response.status);

      // Pega o corpo da resposta como texto para podermos analisar
      const responseBody = await response.text();

      if (!response.ok) {
        // Se a resposta for um erro (ex: 500), o response.ok será false
        console.error("A API retornou um erro:", response.status, responseBody);
        throw new Error(`Erro na API: ${responseBody}`);
      }
      
      // Tenta converter o corpo da resposta em JSON
      const results = JSON.parse(responseBody);
      console.log("Resultado JSON recebido do RPA:", results);

      const updatedList = initialList.map(proc => {
        const foundResult = results.find(res => res.processo === proc.number);
        if (foundResult) {
          return { ...proc, status: 'Consulta Concluída', subsidios: foundResult.subsidios };
        }
        return { ...proc, status: 'Finalizado (sem dados)' };
      });
      setProcessList(updatedList);

    } catch (error) {
      console.error("Falha ao comunicar com o servidor RPA:", error);
      const errorList = initialList.map(proc => ({ ...proc, status: `Falha na comunicação: ${error.message}` }));
      setProcessList(errorList);
    } finally {
      console.log("Processo finalizado (sucesso ou falha).");
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Painel de Consulta - RPA Subsídios</h1>
      </header>
      <main className="panel-container">
        <div className="input-section">
          <h2>Inserir Números de Processo</h2>
          <p>Cole os números dos processos abaixo, um por linha.</p>
          <textarea
            rows="10"
            placeholder="0803535-15.2025.8.20.5013&#10;..."
            value={processInput}
            onChange={(e) => setProcessInput(e.target.value)}
            disabled={isLoading}
          />
          <button onClick={handleStartRPA} disabled={isLoading}>
            {isLoading ? 'Executando RPA...' : 'Consultar Processos'}
          </button>
        </div>
        
        <div className="results-section">
          <h2>Resultados da Consulta</h2>
          {processList.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Número do Processo</th>
                  <th>Status do Subsídio</th>
                  <th>Status da Consulta</th>
                </tr>
              </thead>
              <tbody>
                {processList.map((proc, index) => (
                  <tr key={index}>
                    <td>{proc.number}</td>
                    <td>
                      {proc.subsidios && proc.subsidios.length > 0 ? (
                        <ul>
                          {proc.subsidios.map((sub, i) => (
                            <li key={i}>{sub.item}: <strong>{sub.status}</strong></li>
                          ))}
                        </ul>
                      ) : '-'}
                    </td>
                    <td style={{ fontWeight: 'bold' }}>{proc.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>Nenhum processo na fila.</p>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;