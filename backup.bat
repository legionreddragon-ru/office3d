@echo off
echo === СОЗДАНИЕ АРХИВА ОФИСА ===
echo.
cd /d "%~dp0"
echo Создаю архив office3d_backup_%date:~-4%%date:~3,2%%date:~0,2%.zip...
powershell -command "Compress-Archive -Path 'office.py', 'office_ui.py', 'test_office.py', 'config.json', 'knowledge', 'blackboard.json', 'requirements.txt', '.gitignore', '.streamlit' -DestinationPath 'office3d_backup_%date:~-4%%date:~3,2%%date:~0,2%.zip' -Force"
echo.
echo Архив создан: office3d_backup_*.zip
echo Скопируйте его на флешку и храните в безопасном месте (внутри есть файл с паролем).
echo.
pause