@echo off
echo Iniciando o servidor Python (RPA)...

REM Entra na pasta do servidor
cd RPA

REM Ativa o ambiente virtual (venv)
call venv\Scripts\activate.bat

REM Inicia o servidor Python
echo Ambiente ativado. Iniciando server.py...
python server.py