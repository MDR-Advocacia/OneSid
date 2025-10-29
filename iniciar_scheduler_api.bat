@echo off

cd /d %~dp0

chcp 65001

ECHO Iniciando o Agendador Unificado...
call venv\Scripts\activate.bat
cd RPA

echo Ambiente ativado. Iniciando scheduler_unificado.py...
python scheduler_api.py
pause