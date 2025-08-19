document.addEventListener('DOMContentLoaded', () => {
    // Seleciona os elementos da página
    const processoInput = document.getElementById('processoInput');
    const addBtn = document.getElementById('addBtn');
    const processoList = document.getElementById('processoList');
    const copyBtn = document.getElementById('copyBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const clearBtn = document.getElementById('clearBtn');
    const feedback = document.getElementById('feedback');

    // Array para armazenar os números dos processos
    let processos = [];

    // Função para renderizar a lista na tela
    function renderList() {
        processoList.innerHTML = ''; // Limpa a lista atual
        processos.forEach((proc, index) => {
            const li = document.createElement('li');
            li.textContent = proc;
            
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'x';
            deleteBtn.className = 'delete-btn';
            deleteBtn.onclick = () => {
                removeProcesso(index);
            };

            li.appendChild(deleteBtn);
            processoList.appendChild(li);
        });
    }
    
    // Função para adicionar um processo
    function addProcesso() {
        const novoProcesso = processoInput.value.trim();
        if (novoProcesso === '') {
            showFeedback('Por favor, insira um número de processo.', 'error');
            return;
        }
        if (processos.includes(novoProcesso)) {
            showFeedback('Este processo já foi adicionado.', 'error');
            return;
        }
        processos.push(novoProcesso);
        renderList();
        processoInput.value = ''; // Limpa o campo
        processoInput.focus(); // Deixa o cursor pronto para o próximo
        showFeedback(`Processo adicionado! Total: ${processos.length}`, 'success');
    }

    // Função para remover um processo específico
    function removeProcesso(index) {
        processos.splice(index, 1);
        renderList();
        showFeedback('Processo removido.', 'success');
    }

    // Função para mostrar mensagens de feedback
    function showFeedback(message, type) {
        feedback.textContent = message;
        feedback.style.color = type === 'error' ? '#dc3545' : '#28a745';
        setTimeout(() => { feedback.textContent = ''; }, 3000); // Limpa a mensagem após 3 segundos
    }

    // --- Event Listeners para os botões e campo de input ---

    // Adicionar ao clicar no botão
    addBtn.addEventListener('click', addProcesso);

    // Adicionar ao pressionar "Enter" no campo
    processoInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            addProcesso();
        }
    });

    // Limpar toda a lista
    clearBtn.addEventListener('click', () => {
        processos = [];
        renderList();
        showFeedback('Lista limpa!', 'success');
    });

    // Copiar a lista para a área de transferência
    copyBtn.addEventListener('click', () => {
        if (processos.length === 0) {
            showFeedback('A lista está vazia.', 'error');
            return;
        }
        const textoParaCopiar = processos.join('\n');
        navigator.clipboard.writeText(textoParaCopiar).then(() => {
            showFeedback('Lista copiada para a área de transferência!', 'success');
        });
    });

    // Baixar a lista como um arquivo .txt
    downloadBtn.addEventListener('click', () => {
        if (processos.length === 0) {
            showFeedback('A lista está vazia.', 'error');
            return;
        }
        const textoParaDownload = processos.join('\n');
        const blob = new Blob([textoParaDownload], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'lista_processos.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showFeedback('Download do arquivo iniciado!', 'success');
    });
});