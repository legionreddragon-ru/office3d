@echo off
chcp 65001 >nul
set BACKUP_DIR=C:\office3d\backups
set STAMP=%date:~6,4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%
set STAMP=%STAMP: =0%
set BACKUP_NAME=office3d_%STAMP%.zip
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
echo [backup.bat] Создаю архив: %BACKUP_NAME%
powershell -Command "Get-ChildItem 'C:\office3d' -Exclude 'venv','.git','__pycache__','backups' | Compress-Archive -DestinationPath '%BACKUP_DIR%\%BACKUP_NAME%' -Force"
if exist "%BACKUP_DIR%\%BACKUP_NAME%" (
    echo [backup.bat] OK: %BACKUP_NAME%
) else (
    echo [backup.bat] ОШИБКА: архив не создан
    exit /b 1
)