const API_BASE_URL = 'http://192.168.0.65:5000'; // Ou o endereço do seu backend

// Função auxiliar para fazer requisições autenticadas
const fetchAuth = async (url, options = {}) => {
    const token = localStorage.getItem('userToken');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${url}`, { ...options, headers });

    if (!response.ok) {
        // Tenta extrair uma mensagem de erro do backend
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.msg || `HTTP error! status: ${response.status}`);
    }

    return response.json();
};

// --- Funções da API ---

export const login = (username, password) => {
    return fetchAuth('/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
    });
};

export const getPainelData = () => fetchAuth('/painel');

export const getHistoryData = () => fetchAuth('/historico');

export const runMonitoring = () => fetchAuth('/run-monitoring', { method: 'POST' });

export const archiveProcess = (numero_processo) => {
    return fetchAuth('/arquivar-processo', {
        method: 'POST',
        body: JSON.stringify({ numero_processo }),
    });
};

// --- API de Itens para ADMIN ---
export const getItensRelevantesAdmin = () => fetchAuth('/itens-relevantes');

export const saveItensRelevantesAdmin = (itens) => {
    return fetchAuth('/itens-relevantes', {
        method: 'POST',
        body: JSON.stringify({ itens }),
    });
};

// --- API de Itens para USUÁRIO ---
export const getPreferenciasUsuario = () => fetchAuth('/preferencias-usuario');

export const updatePreferenciaUsuario = (item_id, is_enabled) => {
    return fetchAuth('/preferencias-usuario', {
        method: 'PUT',
        body: JSON.stringify({ item_id, is_enabled }),
    });
};