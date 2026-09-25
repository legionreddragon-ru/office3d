@echo off
echo === РАЗВЁРТЫВАНИЕ ОФИСА НА НОВОМ ПК ===
echo.
echo УБЕДИТЕСЬ, ЧТО НА НОВОМ ПК УСТАНОВЛЕНЫ:
echo   1. Python 3.11+ (python.org/downloads)
echo   2. Ollama (ollama.com/download)
echo   3. Модели: ollama pull qwen2.5:7b, ollama pull phi3:mini
echo.
echo Распакуйте архив office3d_backup_*.zip в любую папку, например C:\office3d
echo.
echo Устанавливаю зависимости...
cd /d "%~dp0"
python -m venv venv
venv\Scripts\pip.exe install -r requirements.txt
echo.
echo Запускаю офис...
start "" "%~dp0ОФИС_VENV.bat"
echo.
echo Офис запущен! Откройте браузер: http://localhost:8501
pause