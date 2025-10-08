// Substitua todo o conteúdo de painel-rpa/src/api.js por este código:

const API_BASE_URL = 'http://localhost:5000/api';

// Função auxiliar para lidar com as respostas da API
async function handleResponse(response) {
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || `Erro HTTP: ${response.status}`);
    }
    return data;
}

// --- Funções de Autenticação ---
export async function login(username, password) {
    // Adicionamos 'credentials: "include"' para que o navegador envie e receba cookies
    const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include', // <-- MUDANÇA IMPORTANTE
    });
    return handleResponse(response);
}

export async function logout() {
    const response = await fetch(`${API_BASE_URL}/logout`, { 
        method: 'POST',
        credentials: 'include', // <-- MUDANÇA IMPORTANTE
    });
    return handleResponse(response);
}

export async function checkLoginStatus() {
    const response = await fetch(`${API_BASE_URL}/profile`, {
        credentials: 'include', // <-- MUDANÇA IMPORTANTE
    });
    return handleResponse(response);
}


// --- Funções de Processos ---
export async function fetchPainelData() {
    const response = await fetch(`${API_BASE_URL}/painel`, {
        credentials: 'include', // <-- MUDANÇA IMPORTANTE
    });
    return handleResponse(response);
}

export async function addSingleProcess(processData) {
    const response = await fetch(`${API_BASE_URL}/add-process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(processData),
        credentials: 'include', // <-- MUDANÇA IMPORTANTE
    });
    return handleResponse(response);
}

export async function importFromLegalOne() {
    const response = await fetch(`${API_BASE_URL}/import-legal-one`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // <-- MUDANÇA IMPORTANTE
    });
    return handleResponse(response);
}