-----

# **OneSid - Painel de Monitoramento de Subsídios**

## **Visão Geral**

O OneSid é uma aplicação full-stack projetada para automatizar a consulta de subsídios processuais em um portal jurídico. A ferramenta consiste em um robô (RPA) que realiza a consulta e um painel de controle web para gerenciar e visualizar os dados.

O sistema permite que os usuários submetam listas de processos para serem monitorados. O robô acessa o portal, extrai o status atual dos subsídios de cada processo e armazena os resultados em um banco de dados local. O painel web exibe os processos em andamento, permitindo que os usuários acompanhem o status, visualizem detalhes e arquivem processos concluídos.

## **Funcionalidades Principais**

  * **Automação de Login e Navegação:** O robô utiliza a biblioteca Playwright para se conectar a uma sessão do navegador, realizar o login através de uma extensão e navegar até as páginas dos processos.
  * **Extração de Dados:** Extrai de forma inteligente o status de cada subsídio de um processo, adaptando-se a diferentes layouts de tabela.
  * **Painel de Controle Web:** Uma interface construída em React para gerenciar todo o fluxo:
      * **Submissão em Lote:** Permite colar listas de processos copiadas de planilhas, associando cada um a um responsável principal.
      * **Monitoramento Contínuo:** Um botão para re-executar a consulta para todos os processos que ainda não foram concluídos.
      * **Visualização Detalhada:** Um modal exibe os detalhes de cada subsídio consultado pelo RPA.
      * **Filtro e Ordenação:** A tabela principal pode ser filtrada dinamicamente e ordenada por ID ou data.
  * **Gestão de Status:** O sistema classifica automaticamente os processos como "Em Monitoramento" ou "Pendente Ciência" com base nos dados extraídos.
  * **Histórico:** Processos concluídos podem ser "cientificados" e movidos para uma área de histórico, mantendo o painel de controle limpo.
  * **Persistência de Dados:** Todas as informações são salvas em um banco de dados SQLite local, garantindo que os dados não sejam perdidos entre as sessões.

## **Tecnologias Utilizadas**

  * **Back-end (RPA e API):**
      * **Python:** Linguagem principal para o robô e o servidor.
      * **Playwright:** Para automação e controle do navegador.
      * **Flask:** Para criar a API REST que conecta o robô ao painel web.
      * **SQLite:** Banco de dados relacional para armazenamento persistente dos dados.
  * **Front-end (Painel):**
      * **React:** Biblioteca JavaScript para construir a interface de usuário.
      * **HTML5 & CSS3:** Para estruturação e estilização do painel.
      * **JavaScript (ES6+):** Para a lógica do painel.

## **Estrutura do Projeto**

```
/
├── bd/
│   └── database.py             # Módulo de controle do banco de dados SQLite
├── painel-rpa/                 # Projeto do front-end em React
│   ├── public/                 # Arquivos estáticos (index.html, favicon)
│   └── src/                    # Código fonte do painel
│       ├── assets/             # Imagens e logos
│       ├── App.css             # Estilos do componente principal
│       ├── App.js              # Componente principal da aplicação
│       └── index.js            # Ponto de entrada do React
├── RPA/
│   ├── abrir_chrome.bat        # Script para iniciar o Chrome com modo de depuração
│   ├── config.py               # Configurações do RPA (URLs, caminhos)
│   ├── main.py                 # Orquestrador da execução do robô
│   ├── navegador.py            # Funções para controlar o navegador
│   ├── portal_bb.py            # Lógica de login no portal
│   ├── processo.py             # Lógica de navegação e extração de dados
│   └── server.py               # Servidor Flask (API)
└── README.md                   # Este arquivo
```

## **Pré-requisitos**

1.  **Python 3.8+** instalado.
2.  **Node.js e npm** instalados.
3.  **Google Chrome** instalado.
4.  Uma **extensão de login** configurada no Chrome (a URL deve ser atualizada no arquivo `RPA/config.py`).

## **Instalação e Configuração**

### **1. Configurar o Perfil do Chrome**

O RPA precisa de um perfil de usuário dedicado no Chrome para manter o login ativo.

  * No arquivo `RPA/abrir_chrome.bat`, verifique se o caminho para o executável do Chrome está correto para a sua máquina.
  * O perfil será criado em `C:\temp\chrome-perfil`. Se desejar, altere este caminho no mesmo arquivo.

### **2. Configurar o Back-end (Python)**

1.  Navegue até a pasta raiz do projeto no seu terminal.
2.  Crie um ambiente virtual (recomendado):
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
3.  Instale as dependências Python:
    ```bash
    pip install Flask Flask-Cors playwright
    ```
4.  Instale os navegadores para o Playwright:
    ```bash
    playwright install
    ```

### **3. Configurar o Front-end (React)**

1.  Abra um **novo terminal**.
2.  Navegue até a pasta do painel:
    ```bash
    cd painel-rpa
    ```
3.  Instale as dependências do Node.js:
    ```bash
    npm install
    ```

## **Como Executar a Aplicação**

Para o sistema funcionar, os dois servidores (back-end e front-end) precisam estar rodando simultaneamente.

1.  **Iniciar o Back-end (Servidor Python):**

      * No terminal com o ambiente virtual ativado, navegue até a pasta `RPA`.
      * Execute o servidor Flask:
        ```bash
        python server.py
        ```
      * O terminal deverá exibir que o banco de dados foi inicializado e que o servidor está rodando. **Mantenha este terminal aberto.**

2.  **Iniciar o Front-end (Painel React):**

      * No segundo terminal, dentro da pasta `painel-rpa`, execute:
        ```bash
        npm start
        ```
      * Seu navegador abrirá automaticamente no endereço `http://localhost:3000` com o painel pronto para uso.

## **Como Usar o Painel**

1.  **Primeiro Login:** Execute o arquivo `RPA/abrir_chrome.bat`. Uma nova janela do Chrome abrirá. Faça o login no portal manualmente pela primeira vez. Você pode fechar o `pause` no terminal do `.bat` depois disso.
2.  **Submeter Processos:** Copie uma lista de uma planilha (no formato `Responsável [TAB] Número do Processo`) e cole na área de texto.
3.  **Adicionar e Consultar:** Clique no botão **"Adicionar e Consultar Novos"**. O RPA será executado em segundo plano para os processos que você colou, e o painel será atualizado com os resultados.
4.  **Rodar Monitoramento:** Clique no botão **"Rodar Monitoramento"** para que o RPA consulte novamente todos os processos que estão com o status "Em Monitoramento".
5.  **Ver Detalhes:** Clique no número de um processo no "Painel de Controle" para abrir um modal com os detalhes dos subsídios encontrados na última consulta.
6.  **Dar Ciência:** Quando um processo estiver com o status "Pendente Ciência", o botão "Dar Ciência" aparecerá. Ao clicar, o processo será movido para a tabela de "Histórico".