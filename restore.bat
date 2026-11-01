@echo off
chcp 65001 >nul
echo === RESTORE OFFICE 3D ===
echo.
set BACKUP_DIR=C:\office3d\backups
echo Последние бэкапы:
dir /b "%BACKUP_DIR%\office3d_*.zip" 2>nul
echo.
set /p FILENAME="Имя файла бэкапа: "
if not exist "%BACKUP_DIR%\%FILENAME%" (
    echo ❌ Не найден: %BACKUP_DIR%\%FILENAME%
    pause
    exit /b
)
echo ВНИМАНИЕ! Текущие файлы будут перезаписаны!
set /p CONFIRM="Продолжить? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Отменено.
    pause
    exit /b
)
powershell -Command "Expand-Archive -Path '%BACKUP_DIR%\%FILENAME%' -DestinationPath 'C:\office3d' -Force"
echo ✅ Восстановление завершено
pause