# **OneSid - Painel de Monitoramento de Subsídios**

## **Visão Geral**

O OneSid é uma aplicação full-stack segura, projetada para automatizar e gerenciar a consulta de subsídios processuais em um portal jurídico. A ferramenta consiste em um robô (RPA) que realiza a consulta e um painel de controle web moderno para gerenciar, visualizar e exportar os dados.

O sistema permite que os usuários, após autenticação, submetam listas de processos para monitoramento. O robô acessa o portal, extrai o status atual dos subsídios de cada processo e armazena os resultados em um banco de dados. O painel web, com uma interface intuitiva estilo *glassmorphism*, exibe os processos em andamento, permitindo o acompanhamento de status, visualização de detalhes (incluindo subsídios pendentes), arquivamento de processos e exportação de dados para planilhas Excel.

## **Funcionalidades Principais**

* **Sistema de Autenticação:** Acesso seguro ao painel através de uma tela de login com autenticação baseada em tokens (JWT).
* **Automação de Login e Navegação:** O robô utiliza a biblioteca Playwright para se conectar a uma sessão do navegador, realizar o login no portal através de uma extensão e navegar até as páginas dos processos.
* **Extração Inteligente de Dados:** Extrai de forma robusta o status de cada subsídio de um processo, adaptando-se a diferentes layouts de tabela.
* **Painel de Controle Web Moderno:** Uma interface construída em React com design *liquid glass*:
    * **Submissão em Lote:** Permite colar listas de processos copiadas de planilhas, associando cada um a um responsável principal e uma classificação.
    * **Gerenciador de Itens Relevantes:** Um CRUD (Criar, Ler, Atualizar, Deletar) em um modal para definir quais subsídios são prioritários para o monitoramento.
    * **Monitoramento Contínuo:** Um botão para re-executar a consulta para todos os processos que ainda não foram concluídos.
    * **Visualização Detalhada:** Um modal exibe os detalhes de cada subsídio encontrado pelo RPA, além de destacar quais dos itens relevantes ainda estão pendentes.
    * **Filtro e Ordenação Avançada:** A tabela principal pode ser filtrada dinamicamente por responsável, número do processo ou classificação, e ordenada por ID, data ou status.
    * **Paginação:** A tabela de dados principal é paginada, permitindo a exibição de 10, 25, 50 ou 100 itens por página para melhor performance.
    * **Exportação para Excel:** Um botão exporta os dados do painel de controle e do histórico para uma planilha `.xlsx` com abas separadas.
* **Gestão de Status Inteligente:** O sistema classifica automaticamente os processos como "Em Monitoramento" ou "Pendente Ciência" com base nos dados extraídos e nos itens relevantes definidos.
* **Histórico:** Processos concluídos podem ser "cientificados" e movidos para uma área de histórico, mantendo o painel de controle limpo e organizado.
* **Persistência de Dados:** Todas as informações são salvas em um banco de dados SQLite local, garantindo que os dados não sejam perdidos entre as sessões.

## **Tecnologias Utilizadas**

* **Back-end (RPA e API):**
    * **Python:** Linguagem principal para o robô e o servidor.
    * **Playwright:** Para automação e controle do navegador.
    * **Flask:** Para criar a API REST que conecta o robô ao painel web.
    * **Flask-JWT-Extended:** Para a implementação da autenticação com tokens JWT.
    * **Werkzeug:** Para a criptografia segura de senhas (hashing).
    * **OpenPyXL:** Para a geração de planilhas Excel (`.xlsx`).
    * **SQLite:** Banco de dados relacional para armazenamento dos dados.
* **Front-end (Painel):**
    * **React:** Biblioteca JavaScript para construir a interface de usuário.
    * **React Router:** Para gerenciar a navegação entre a tela de login e o painel.
    * **HTML5 & CSS3:** Para estruturação e estilização do painel.
    * **JavaScript (ES6+):** Para a lógica do painel.

## **Estrutura do Projeto**
(A estrutura do projeto permanece a mesma)

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
    pip install Flask Flask-Cors playwright Flask-JWT-Extended Werkzeug openpyxl
    ```
4.  Instale os navegadores para o Playwright:
    ```bash
    playwright install
    ```
5.  **(Primeira Execução)** Ao iniciar o servidor pela primeira vez, um usuário padrão `admin` com senha `admin` será criado. Você pode alterar isso ou adicionar novos usuários diretamente no código do arquivo `bd/database.py` na função `inicializar_banco()`.

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
    * Seu navegador abrirá automaticamente no endereço `http://localhost:3000` com a tela de login.

## **Como Usar o Painel**

1.  **Login na Aplicação:** Acesse `http://localhost:3000` e utilize um usuário e senha cadastrados (usuário padrão: `admin`, senha: `admin`).
2.  **Primeiro Login no Portal Jurídico:** Execute o arquivo `RPA/abrir_chrome.bat`. Uma nova janela do Chrome abrirá. Faça o login no portal manualmente pela primeira vez para que a sessão fique salva. Você pode fechar a janela do `pause` no terminal do `.bat` depois disso.
3.  **Definir Itens Relevantes:** No painel, clique em "Definir Itens" no cabeçalho para adicionar ou remover os subsídios que são cruciais para o monitoramento.
4.  **Submeter Processos:** Copie uma lista de uma planilha (no formato `Escritório [TAB] Responsável [TAB] Processo [TAB] Classificação`) e cole na área de texto.
5.  **Adicionar e Consultar:** Clique em **"Adicionar e Consultar Novos"**. O RPA será executado em segundo plano, e o painel será atualizado com os resultados.
6.  **Rodar Monitoramento:** Clique em **"Rodar Monitoramento"** para que o RPA consulte novamente todos os processos que estão com o status "Em Monitoramento".
7.  **Ver Detalhes:** Clique no número de um processo para abrir um modal com os detalhes dos subsídios encontrados e dos itens relevantes que ainda estão pendentes.
8.  **Dar Ciência:** Quando um processo estiver com o status "Pendente Ciência", o botão "Dar Ciência" aparecerá. Ao clicar, o processo será movido para o Histórico.