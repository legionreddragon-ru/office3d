@echo off
chcp 65001 >nul
echo === BACKUP OFFICE 3D ===
echo.
set BACKUP_DIR=C:\office3d\backups
set STAMP=%date:~6,4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%
set STAMP=%STAMP: =0%
set BACKUP_NAME=office3d_%STAMP%.zip
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
echo Создаю резервную копию: %BACKUP_NAME%
powershell -Command "Get-ChildItem 'C:\office3d' -Exclude 'venv','.git','__pycache__','backups' | Compress-Archive -DestinationPath '%BACKUP_DIR%\%BACKUP_NAME%' -Force"
if exist "%BACKUP_DIR%\%BACKUP_NAME%" (
    echo ✅ Бэкап создан: %BACKUP_DIR%\%BACKUP_NAME%
) else (
    echo ❌ ОШИБКА: бэкап НЕ создан, пришли мне этот экран
)
pause