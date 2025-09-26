-----

# OneSid - Painel de Monitoramento de Subsídios

O OneSid é uma aplicação full-stack projetada para automatizar a verificação de subsídios processuais em portais jurídicos. A solução combina um robô (RPA) para a extração de dados, uma API robusta como back-end e um painel de controle interativo como front-end.

## Funcionalidades Principais

  - **Automação Inteligente (RPA):** O robô, construído com Python e Playwright, realiza o login no portal, navega até a área de subsídios e extrai o status de cada item de uma lista de processos.
  - **Painel de Controle Intuitivo (Front-end):** Interface web moderna feita com React para:
      - **Login de Usuário:** Acesso seguro e individualizado.
      - **Visualização Clara:** Processos são exibidos com status `Monitorando` ou `Pendente Ciência`.
      - **Gestão de Processos:** Inclusão de novos processos em lote (copiar e colar do Excel) e gerenciamento dos existentes.
      - **Filtros e Ordenação:** Encontre facilmente os processos que você procura.
      - **Exportação para Excel:** Exporte a visualização atual do painel ou o histórico de processos arquivados.
  - **Notificação de "Pendente Ciência":** Um processo muda seu status para `Pendente Ciência` quando **todos os itens de interesse do usuário que existem naquele processo** são marcados como "Concluído" pelo robô. Isso permite que o usuário foque apenas no que é relevante.
  - **Preferências Personalizadas:** Cada usuário pode definir sua própria lista de "itens de interesse" para monitoramento.
  - **Back-end e Banco de Dados:** Uma API em Flask (Python) gerencia as requisições, e um banco de dados SQLite armazena todos os dados de forma persistente.

## Tecnologias Utilizadas

  - **Back-end:**
      - Python
      - Flask (para a API REST)
      - Playwright (para o RPA)
      - SQLite (para o banco de dados)
  - **Front-end:**
      - React.js
      - Axios (para comunicação com a API)
  - **Linguagem:** JavaScript

## Como Executar o Projeto

### Pré-requisitos

  - Node.js e npm (para o Front-end)
  - Python 3 (para o Back-end e RPA)

### 1\. Instalação do Back-end (RPA e Servidor)

Navegue até a pasta `RPA/` e instale as dependências do Python:

```bash
cd RPA
pip install -r requirements.txt
```

Após a instalação, instale os navegadores para o Playwright:

```bash
playwright install
```

### 2\. Instalação do Front-end (Painel)

Em outro terminal, navegue até a pasta `painel-rpa/` e instale as dependências do Node.js:

```bash
cd painel-rpa
npm install
```

### 3\. Executando a Aplicação

Para facilitar, você pode usar o script `iniciar_painel.bat` na raiz do projeto. Ele se encarregará de iniciar o servidor back-end e o cliente front-end simultaneamente.

Basta dar um duplo clique no arquivo:

  - `iniciar_painel.bat`

O script executará os seguintes comandos:

  - **API (Back-end):** `python RPA/server.py`
  - **Painel (Front-end):** `npm start` dentro da pasta `painel-rpa`

Após a execução, o painel será aberto automaticamente no seu navegador, geralmente em `http://localhost:3000`.

