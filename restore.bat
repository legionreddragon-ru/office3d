@echo off
echo === РАЗВЁРТЫВАНИЕ ОФИСА НА НОВОМ ПК ===
echo.
echo УБЕДИТЕСЬ, ЧТО НА НОВОМ ПК УСТАНОВЛЕНЫ:
echo   1. Python 3.12+ (python.org/downloads)
echo   2. Ollama (ollama.com/download)
echo   3. Модели: ollama pull qwen2.5:7b, ollama pull phi3:mini
echo.
echo Распакуйте архив office3d_backup_*.zip в C:\office3d
echo.
echo Устанавливаю зависимости...
pip install streamlit requests duckduckgo_search beautifulsoup4
echo.
echo Запускаю офис...
cd /d C:\office3d
start "" "C:\office3d\ОФИС.bat"
echo.
echo Офис запущен! Откройте браузер: http://localhost:8501
pause