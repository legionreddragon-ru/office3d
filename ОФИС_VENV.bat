@echo off
chcp 65001 >nul
title ОФИС-3D (venv)
echo =============================================
echo  ОФИС-3D — виртуальное окружение
echo =============================================
echo.

cd /d "%~dp0"

echo [1/3] Проверяю Ollama...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Ollama не запущен. Запускаю в фоне...
    start /b ollama serve
    timeout /t 5 /nobreak >nul
) else (
    echo Ollama уже работает.
)

echo [2/3] Активирую виртуальное окружение...
call "%~dp0venv\Scripts\activate.bat"

echo [3/3] Запускаю панель офиса...
echo.
echo Откроется браузер: http://localhost:8501
echo Не закрывайте это окно!
echo.

start http://localhost:8501
streamlit run office_ui.py --server.headless true --server.port 8501 --server.address 127.0.0.1

pause