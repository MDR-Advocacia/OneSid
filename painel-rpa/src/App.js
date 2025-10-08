// Substitua todo o conteúdo de painel-rpa/src/App.js por este código:

import React, { useState, useEffect } from 'react';
import {
    fetchPainelData,
    addSingleProcess,
    checkLoginStatus,
    logout,
    importFromLegalOne,
    exportToJson // Importamos a nova função
} from './api';
import LoginPage from './LoginPage';
import './App.css';
import logo from './assets/logo-onesid.png';

const DetailsModal = ({ processo, onClose }) => {
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
                                <tr key={index}><td>{sub.item}</td><td><strong>{sub.status}</strong></td></tr>
                            ))}
                        </tbody>
                    </table>
                ) : (<p>Nenhum subsídio encontrado.</p>)}
                <button className="modal-close-button" onClick={onClose}>Fechar</button>
            </div>
        </div>
    );
};

function App() {
    const [processos, setProcessos] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [user, setUser] = useState(null);
    const [message, setMessage] = useState('');
    const [numeroProcesso, setNumeroProcesso] = useState('');
    const [executante, setExecutante] = useState('');
    const [isImporting, setIsImporting] = useState(false);
    const [selectedProcess, setSelectedProcess] = useState(null);

    // --- NOVO ESTADO PARA EXPORTAÇÃO ---
    const [isExporting, setIsExporting] = useState(false);

    const checkAuth = async () => {
        try {
            const userData = await checkLoginStatus();
            if (userData && userData.logged_in) {
                setUser(userData);
                loadPainelData();
            } else {
                setUser(null);
            }
        } catch (error) {
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const loadPainelData = async () => {
        setIsLoading(true);
        try {
            const data = await fetchPainelData();
            const dataWithSubsidios = data.map(proc => ({ ...proc, subsidios: proc.subsidios || [] }));
            setProcessos(dataWithSubsidios);
            setError(null);
        } catch (error) {
            setError('Falha ao carregar dados do painel.');
            setProcessos([]);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => { checkAuth(); }, []);

    const handleLoginSuccess = (userData) => {
        setUser(userData);
        loadPainelData();
    };

    const handleLogout = async () => {
        await logout();
        setUser(null);
        setProcessos([]);
    };

    const handleAddProcess = async (e) => {
        e.preventDefault();
        if (!numeroProcesso.trim()) {
            setMessage('Por favor, insira o número do processo.');
            return;
        }
        setMessage('Adicionando...');
        try {
            const response = await addSingleProcess({ numero_processo: numeroProcesso, executante: executante });
            setMessage(response.message);
            setNumeroProcesso('');
            setExecutante('');
            loadPainelData();
        } catch (error) {
            setMessage(error.message || 'Erro ao adicionar processo.');
        }
    };

    const handleImport = async () => {
        setIsImporting(true);
        setMessage('Iniciando importação do Legal One...');
        try {
            const response = await importFromLegalOne();
            setMessage(response.message);
            loadPainelData();
        } catch (error) {
            setMessage(error.message || 'Ocorreu um erro na importação.');
        } finally {
            setIsImporting(false);
        }
    };

    // --- NOVA FUNÇÃO PARA EXPORTAR E BAIXAR O JSON ---
    const handleExport = async () => {
        setIsExporting(true);
        setMessage('Gerando arquivo JSON...');
        try {
            const data = await exportToJson();
            
            // Cria um "Blob" com os dados JSON
            const jsonString = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            
            // Cria um link temporário para o download
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'export_onesid.json'; // Nome do arquivo
            
            // Simula o clique no link para iniciar o download
            document.body.appendChild(link);
            link.click();
            
            // Limpa o link temporário
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            setMessage('Arquivo JSON exportado com sucesso!');
        } catch (error) {
            setMessage(error.message || 'Ocorreu um erro ao exportar o JSON.');
        } finally {
            setIsExporting(false);
        }
    };

    if (!user) {
        return <LoginPage onLoginSuccess={handleLoginSuccess} />;
    }

    return (
        <>
            <DetailsModal processo={selectedProcess} onClose={() => setSelectedProcess(null)} />
            <div className="App">
                <header className="app-header">
                    <img src={logo} alt="OneSid Logo" className="logo" />
                    <div className="user-info">
                        <span>Olá, {user.username}</span>
                        <button onClick={handleLogout} className="logout-button">Sair</button>
                    </div>
                </header>
                
                <main>
                    <div className="actions-container">
                        <div className="form-container card">
                            <h2>Adicionar Processo</h2>
                            <form onSubmit={handleAddProcess} className="add-process-form">
                                <input type="text" value={numeroProcesso} onChange={(e) => setNumeroProcesso(e.target.value)} placeholder="Número do Processo (CNJ)" required />
                                <input type="text" value={executante} onChange={(e) => setExecutante(e.target.value)} placeholder="Nome do Executante" />
                                <button type="submit">Adicionar à Esteira</button>
                            </form>
                        </div>

                        <div className="import-container card">
                            <h2>Ações em Lote</h2>
                            <p>Importe tarefas do Legal One ou exporte os dados de monitoramento.</p>
                            <button onClick={handleImport} disabled={isImporting}>
                                {isImporting ? 'Importando...' : 'Importar do Legal One'}
                            </button>
                            {/* BOTÃO DE EXPORTAR */}
                            <button onClick={handleExport} disabled={isExporting}>
                                {isExporting ? 'Exportando...' : 'Exportar JSON'}
                            </button>
                        </div>
                    </div>

                    {message && <p className="message">{message}</p>}

                    <div className="process-table-container">
                        <h2>Processos em Monitoramento</h2>
                        {isLoading ? <p>Carregando...</p> : error ? <p className="error">{error}</p> : (
                            <table>
                                <thead>
                                    <tr><th>ID</th><th>Número do Processo</th><th>Responsável</th><th>Status</th><th>Última Verificação</th></tr>
                                </thead>
                                <tbody>
                                    {processos.length > 0 ? (
                                        processos.map((p) => (
                                            <tr key={`${p.id}-${p.numero_processo}`}>
                                                <td>{p.id}</td>
                                                <td><button className="link-button" onClick={() => setSelectedProcess(p)}>{p.numero_processo}</button></td>
                                                <td>{p.responsavel_principal}</td>
                                                <td>{p.status_geral}</td>
                                                <td>{new Date(p.data_ultima_atualizacao).toLocaleString('pt-BR')}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr><td colSpan="5">Nenhum processo em monitoramento.</td></tr>
                                    )}
                                </tbody>
                            </table>
                        )}
                    </div>
                </main>
            </div>
        </>
    );
}

export default App;