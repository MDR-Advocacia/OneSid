@echo off
TITLE OneSid - Inicializador

echo ======================================================
echo           INICIANDO O PAINEL ONESID
echo ======================================================
echo.

echo [1/2] Iniciando o servidor do Back-end (Python)...
:: Este comando agora chama o executavel do Python DIRETAMENTE de dentro do venv.
START "OneSid - Servidor Python (Back-end)" cmd /k "cd RPA && .\\venv\\Scripts\\python.exe server.py"

echo [2/2] Iniciando o painel do Front-end (React)...
:: Este comando abre outra janela de terminal e inicia o React na porta 3001 para evitar conflitos.
START "OneSid - Painel React (Front-end)" cmd /k "cd painel-rpa && set PORT=3001 && npm start"

echo.
echo ======================================================
echo    Tudo pronto! Os servidores foram iniciados.
echo.
echo    - O painel abrira no seu navegador em http://localhost:3001
echo    - Voce pode fechar esta janela agora.
echo ======================================================
echo.

pause