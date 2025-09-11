import React, { useState, useEffect, useMemo, useCallback } from 'react';
import LoginPage from './LoginPage';
import './App.css';
import logo from './assets/logo-onesid.png';

const API_BASE_URL = 'http://127.0.0.1:5000';

// --- SEUS COMPONENTES DE MODAL EXISTENTES (sem alterações) ---
const Modal = ({ processo, onClose }) => {
    if (!processo) return null;
    const temSubsidiosEncontrados = processo.subsidios && processo.subsidios.length > 0;
    const temSubsidiosPendentes = processo.subsidios_pendentes && processo.subsidios_pendentes.length > 0;
    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h3>Detalhes do Subsídio - Processo {processo.numero_processo}</h3>
                {temSubsidiosPendentes && (
                    <div className="itens-pendentes-section">
                        <h4>Itens Relevantes Pendentes</h4>
                        <ul>
                            {processo.subsidios_pendentes.map((item, index) => (<li key={index}>{item}</li>))}
                        </ul>
                    </div>
                )}
                {temSubsidiosEncontrados ? (
                    <>
                        <h4>Subsídios Encontrados</h4>
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
                    </>
                ) : <p>Nenhum subsídio encontrado para este processo na última consulta.</p>}
                {!temSubsidiosPendentes && temSubsidiosEncontrados && (
                    <p className="feedback-message">Todos os itens relevantes foram encontrados para este processo.</p>
                )}
                <button className="modal-close-button" onClick={onClose}>Fechar</button>
            </div>
        </div>
    );
};

// --- MODAL DE CONFIGURAÇÕES COM ABAS ---
const SettingsModal = ({ onClose, token, onAuthError, userRole }) => {
    const [activeTab, setActiveTab] = useState('itens');

    const [itens, setItens] = useState([]);
    const [novoItem, setNovoItem] = useState('');
    const [itensStatus, setItensStatus] = useState('Carregando...');

    const [userList, setUserList] = useState([]);
    const [newUsername, setNewUsername] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [newUserRole, setNewUserRole] = useState('user');
    const [userStatus, setUserStatus] = useState('');

    const fetchWithAuth = useCallback(async (url, options = {}) => {
        const headers = { 'Content-Type': 'application/json', ...options.headers, 'Authorization': `Bearer ${token}` };
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            onAuthError();
            throw new Error('Sessão expirada.');
        }
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ msg: "Erro desconhecido" }));
            throw new Error(errorData.msg);
        }
        return response.json();
    }, [token, onAuthError]);

    useEffect(() => {
        const fetchItensData = async () => {
            try {
                setItensStatus('Carregando...');
                if (userRole === 'admin') {
                    const data = await fetchWithAuth(`${API_BASE_URL}/itens-relevantes`);
                    setItens(Array.isArray(data) ? data.map(item => item.item_nome) : []);
                } else {
                    const data = await fetchWithAuth(`${API_BASE_URL}/preferencias-usuario`);
                    setItens(Array.isArray(data) ? data : []);
                }
                setItensStatus('');
            } catch (e) { setItensStatus(`Erro: ${e.message}`); }
        };

        const fetchUsersData = async () => {
            if (userRole === 'admin') {
                try {
                    setUserStatus('Carregando usuários...');
                    const data = await fetchWithAuth(`${API_BASE_URL}/users`);
                    setUserList(Array.isArray(data) ? data : []);
                    setUserStatus('');
                } catch (e) { setUserStatus(`Erro: ${e.message}`); }
            }
        };

        if (activeTab === 'itens') fetchItensData();
        if (activeTab === 'usuarios') fetchUsersData();

    }, [fetchWithAuth, userRole, activeTab]);

    // --- Funções da Aba de ITENS ---
    // ################### AQUI ESTÁ A CORREÇÃO ###################
    const handleAddItem = () => { if (novoItem && !itens.includes(novoItem.trim())) setItens([...itens, novoItem.trim()]); setNovoItem(''); };
    // ###########################################################
    const handleRemoveItem = (itemToRemove) => setItens(itens.filter(item => item !== itemToRemove));
    const handleSaveAdminItems = async () => {
        try {
            setItensStatus('Salvando...');
            await fetchWithAuth(`${API_BASE_URL}/itens-relevantes`, { method: 'POST', body: JSON.stringify({ itens }) });
            setItensStatus('Salvo!');
            setTimeout(onClose, 1000);
        } catch (e) { setItensStatus(`Erro: ${e.message}`); }
    };
    const handleUserPreferenceChange = async (itemId, isEnabled) => {
        setItens(prev => prev.map(item => item.id === itemId ? { ...item, is_enabled: isEnabled } : item));
        try {
            await fetchWithAuth(`${API_BASE_URL}/preferencias-usuario`, { method: 'PUT', body: JSON.stringify({ item_id: itemId, is_enabled: isEnabled }) });
        } catch (e) {
            setItensStatus(`Erro: ${e.message}`);
            setItens(prev => prev.map(item => item.id === itemId ? { ...item, is_enabled: !isEnabled } : item));
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        setUserStatus('Criando usuário...');
        try {
            const result = await fetchWithAuth(`${API_BASE_URL}/users`, {
                method: 'POST',
                body: JSON.stringify({ username: newUsername, password: newPassword, role: newUserRole }),
            });
            setUserStatus(result.msg);
            const data = await fetchWithAuth(`${API_BASE_URL}/users`);
            setUserList(Array.isArray(data) ? data : []);
            setNewUsername('');
            setNewPassword('');
        } catch (e) {
            setUserStatus(`Erro: ${e.message}`);
        }
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content large" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Configurações</h2>
                    {userRole === 'admin' && (
                        <div className="modal-tabs">
                            <button className={`tab-button ${activeTab === 'itens' ? 'active' : ''}`} onClick={() => setActiveTab('itens')}>Itens Relevantes</button>
                            <button className={`tab-button ${activeTab === 'usuarios' ? 'active' : ''}`} onClick={() => setActiveTab('usuarios')}>Gerenciar Usuários</button>
                        </div>
                    )}
                </div>
                {activeTab === 'itens' && (
                    <>
                        <h3>{userRole === 'admin' ? 'Definir Itens Relevantes' : 'Minhas Preferências de Itens'}</h3>
                        <p>{userRole === 'admin' ? 'Adicione ou remova itens da lista mestra.' : 'Habilite ou desabilite os itens que deseja monitorar.'}</p>
                        {userRole === 'admin' ? (
                            <div className="item-manager">
                                <div className="item-add-form">
                                    <input type="text" value={novoItem} onChange={(e) => setNovoItem(e.target.value)} placeholder="Digite o nome do novo item..." onKeyPress={(e) => e.key === 'Enter' && handleAddItem()} />
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
                        ) : (
                            <div className="preferences-list">
                                {itens.map(item => (
                                    <div key={item.id} className="preference-item">
                                        <span>{item.item_nome}</span>
                                        <label className="toggle-switch">
                                            <input type="checkbox" checked={item.is_enabled} onChange={(e) => handleUserPreferenceChange(item.id, e.target.checked)} />
                                            <span className="slider"></span>
                                        </label>
                                    </div>
                                ))}
                            </div>
                        )}
                        <div className="modal-actions">
                            <span className="feedback-message">{itensStatus}</span>
                            {userRole === 'admin' && <button onClick={handleSaveAdminItems} className="primary-button">Salvar</button>}
                            <button onClick={onClose} className="secondary-button">Fechar</button>
                        </div>
                    </>
                )}
                {activeTab === 'usuarios' && userRole === 'admin' && (
                    <div className="user-management-grid">
                        <div className="user-list">
                            <h4>Usuários Existentes</h4>
                            <ul>
                                {userList.map(user => (
                                    <li key={user.id}>
                                        <span>{user.username}</span>
                                        <span className="user-role">{user.role}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="user-form">
                            <h4>Criar Novo Usuário</h4>
                            <form onSubmit={handleCreateUser}>
                                <div className="form-group">
                                    <label htmlFor="username">Nome de Usuário</label>
                                    <input type="text" id="username" value={newUsername} onChange={e => setNewUsername(e.target.value)} required />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="password">Senha</label>
                                    <input type="password" id="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="role">Permissão</label>
                                    <select id="role" value={newUserRole} onChange={e => setNewUserRole(e.target.value)}>
                                        <option value="user">Usuário</option>
                                        <option value="admin">Administrador</option>
                                    </select>
                                </div>
                                <button type="submit" className="primary-button">Criar Usuário</button>
                                <span className="feedback-message" style={{ marginLeft: '15px' }}>{userStatus}</span>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// --- SEU COMPONENTE DASHBOARD (sem alterações) ---
const Dashboard = ({ token, onLogout, userRole }) => {
    const [processInput, setProcessInput] = useState('');
    const [panelList, setPanelList] = useState([]);
    const [historyList, setHistoryList] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [modalProcess, setModalProcess] = useState(null);
    const [filters, setFilters] = useState({ responsavel: '', numero_processo: '', classificacao: '' });
    const [sortConfig, setSortConfig] = useState({ key: 'id', direction: 'descending' });
    const [showSettingsModal, setShowSettingsModal] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);

    const fetchWithAuth = useCallback(async (url, options = {}) => {
        const headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            onLogout();
            throw new Error('Sessão expirada.');
        }
        return response;
    }, [token, onLogout]);

    const fetchData = useCallback(async () => {
        try {
            const panelResponse = await fetchWithAuth(`${API_BASE_URL}/painel`);
            const panelData = await panelResponse.json();
            setPanelList(Array.isArray(panelData) ? panelData : []);

            const historyResponse = await fetchWithAuth(`${API_BASE_URL}/historico`);
            const historyData = await historyResponse.json();
            setHistoryList(Array.isArray(historyData) ? historyData : []);
        } catch (error) {
            console.error("Falha ao buscar dados:", error);
            setMessage('Erro de conexão ou sessão expirada.');
        }
    }, [fetchWithAuth]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleAddAndRun = async () => {
        const lines = processInput.split('\n').filter(line => line.trim() !== '');
        if (lines.length === 0) {
            setMessage('Por favor, insira os dados no formato correto.');
            return;
        }
        const processosParaEnviar = lines.map(line => {
            const parts = line.split('\t');
            if (parts.length >= 4) {
                return { responsavel: parts[1].trim(), numero: parts[2].trim(), classificacao: parts[3].trim() };
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
            const response = await fetchWithAuth(`${API_BASE_URL}/add-and-run`, {
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
            const response = await fetchWithAuth(`${API_BASE_URL}/run-monitoring`, { method: 'POST' });
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
            const response = await fetchWithAuth(`${API_BASE_URL}/arquivar-processo`, {
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
    const handleExport = async () => {
        setMessage('Gerando planilha...');
        setIsLoading(true);
        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/export-excel`);
            if (!response.ok) {
                throw new Error('Falha ao gerar o arquivo no servidor.');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'onesid_export.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            setMessage('Planilha exportada com sucesso!');
        } catch (error) {
            console.error("Erro ao exportar:", error);
            setMessage('Erro ao exportar a planilha.');
        } finally {
            setIsLoading(false);
        }
    };
    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFilters(prevFilters => ({ ...prevFilters, [name]: value }));
        setCurrentPage(1);
    };
    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
        setCurrentPage(1);
    };

    const getSortIcon = (name) => {
        if (sortConfig.key !== name) return null;
        return sortConfig.direction === 'ascending' ? ' ▲' : ' ▼';
    };
    const sortedAndFilteredPanelList = useMemo(() => {
        let list = [...panelList];
        list = list.filter(proc =>
            (proc.responsavel_principal?.toLowerCase().includes(filters.responsavel.toLowerCase()) ?? true) &&
            proc.numero_processo.toLowerCase().includes(filters.numero_processo.toLowerCase()) &&
            (proc.classificacao?.toLowerCase().includes(filters.classificacao.toLowerCase()) ?? true)
        );
        if (sortConfig.key !== null) {
            list.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'ascending' ? -1 : 1;
                if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'ascending' ? 1 : -1;
                return 0;
            });
        }
        return list;
    }, [panelList, filters, sortConfig]);
    const paginatedList = useMemo(() => {
        const startIndex = (currentPage - 1) * itemsPerPage;
        return sortedAndFilteredPanelList.slice(startIndex, startIndex + itemsPerPage);
    }, [sortedAndFilteredPanelList, currentPage, itemsPerPage]);
    const totalPages = Math.ceil(sortedAndFilteredPanelList.length / itemsPerPage);


    return (
        <>
            {showSettingsModal && <SettingsModal onClose={() => setShowSettingsModal(false)} token={token} onAuthError={onLogout} userRole={userRole} />}
            <Modal processo={modalProcess} onClose={() => setModalProcess(null)} />
            <div className="App">
                <header className="App-header">
                    <img src={logo} className="header-logo" alt="Logo OneSid" />
                    <h1>OneSid</h1>
                    <div>
                        <button className="header-button" onClick={() => setShowSettingsModal(true)}>Configurações</button>
                        <button className="header-button" onClick={onLogout} style={{ marginLeft: '10px' }}>Sair</button>
                    </div>
                </header>
                <main className="panel-container">
                    <div className="input-section">
                        <h2>Submeter Novos Processos</h2>
                        <p>Copie e cole da sua planilha (as 4 colunas).</p>
                        <textarea rows="8" placeholder="Escritório [TAB] Responsável [TAB] Processo [TAB] Classificação" value={processInput} onChange={(e) => setProcessInput(e.target.value)} disabled={isLoading} />
                        <div className="button-group">
                            <button onClick={handleAddAndRun} disabled={isLoading}>{isLoading ? 'Aguarde...' : 'Adicionar e Consultar Novos'}</button>
                            <button onClick={handleRunMonitoring} disabled={isLoading} className="secondary-button">{isLoading ? 'Aguarde...' : "Rodar Monitoramento"}</button>
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
                        <div className="export-button-container">
                            <button onClick={handleExport} disabled={isLoading} className="secondary-button">{isLoading ? 'Exportando...' : 'Exportar para Excel'}</button>
                        </div>
                        <div className="pagination-controls">
                            <span>Exibir:</span>
                            <select value={itemsPerPage} onChange={(e) => { setItemsPerPage(Number(e.target.value)); setCurrentPage(1); }}>
                                <option value={10}>10</option>
                                <option value={25}>25</option>
                                <option value={50}>50</option>
                                <option value={100}>100</option>
                            </select>
                            <div className="page-navigation">
                                <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>Anterior</button>
                                <span>Página {currentPage} de {totalPages || 1}</span>
                                <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages || totalPages === 0}>Próxima</button>
                            </div>
                        </div>
                        {paginatedList.length > 0 ? (
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
                                    {paginatedList.map((proc) => (
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
};

// --- SEU COMPONENTE APP (sem alterações) ---
function App() {
    const [token, setToken] = useState(localStorage.getItem('user_token'));
    const [userRole, setUserRole] = useState(localStorage.getItem('user_role'));

    const handleLoginSuccess = (newToken, role) => {
        localStorage.setItem('user_token', newToken);
        localStorage.setItem('user_role', role);
        setToken(newToken);
        setUserRole(role);
    };

    const handleLogout = () => {
        localStorage.removeItem('user_token');
        localStorage.removeItem('user_role');
        setToken(null);
        setUserRole(null);
    };

    return (
        token && userRole
            ? <Dashboard token={token} onLogout={handleLogout} userRole={userRole} />
            : <LoginPage onLoginSuccess={handleLoginSuccess} />
    );
}

export default App;