@echo off
echo === СОЗДАНИЕ АРХИВА ОФИСА ===
echo.
cd /d C:\office3d
echo Создаю архив office3d_backup_%date:~-4%%date:~3,2%%date:~0,2%.zip...
powershell -command "Compress-Archive -Path 'office.py', 'office_ui.py', 'test_office.py', 'config.json', 'knowledge', 'logs', 'reports', '.streamlit' -DestinationPath 'office3d_backup_%date:~-4%%date:~3,2%%date:~0,2%.zip' -Force"
echo.
echo Архив создан: office3d_backup_*.zip
echo Скопируйте его на флешку.
echo.
pause