@echo off
rem Change le répertoire courant vers celui du script
cd /d "%~dp0"

rem Lancer le script Python
python manage_site.py
pause