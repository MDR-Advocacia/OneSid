@echo off
echo Iniciando o Scheduler Python (RPA)...

REM Entra na pasta do servidor
cd RPA

REM Ativa o ambiente virtual (venv)
call venv\Scripts\activate.bat

REM Inicia o scheduler
echo Ambiente ativado. Iniciando scheduler.py...
python scheduler.py