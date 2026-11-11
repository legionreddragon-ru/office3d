@echo off
chcp 65001 >nul
cd /d C:\office3d
echo.
echo ========================================================
echo   УМНЫЙ БЭКАП (сначала диагностика, потом копия)
echo ========================================================
echo.
echo [1/4] Запуск диагностики (checkall silent)...
echo.
venv\Scripts\python.exe checkall.py silent
if %ERRORLEVEL% EQU 0 goto :healthy

echo.
echo [2/4] Есть ошибки. Пытаюсь автолечение...
venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'.'); import checkall; checkall.try_heal(); [print('  🔧 ' + h) for h in checkall.healed] if checkall.healed else print('  (авлечение ничего не нашло)')"
echo.
echo [3/4] Повторная диагностика после лечения...
echo.
venv\Scripts\python.exe checkall.py silent
if %ERRORLEVEL% EQU 0 goto :healthy

echo.
echo ========================================================
echo   ❌ ОСТАЛИСЬ ОШИБКИ, бэкап ОТМЕНЁН
echo ========================================================
echo    Исправь проблемы вручную и запусти снова.
echo.
pause
exit /b 1

:healthy
echo.
echo ========================================================
echo   ✅ ОФИС ЗДОРОВ, делаю безопасный бэкап
echo ========================================================
echo.
call backup.bat
echo.
echo ========================================================
echo   ✅ БЕЗОПАСНЫЙ БЭКАП ГОТОВ
echo ========================================================
echo.
pause