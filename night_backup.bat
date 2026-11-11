@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d C:\office3d
set LOG=backups\night_log.txt
if not exist backups mkdir backups
echo === %date% %time% === >> %LOG%
venv\Scripts\python.exe checkall.py silent >> %LOG% 2>&1
if %ERRORLEVEL% EQU 0 goto :do_backup
venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'.'); import checkall; checkall.try_heal()" >> %LOG% 2>&1
venv\Scripts\python.exe checkall.py silent >> %LOG% 2>&1
if %ERRORLEVEL% EQU 0 goto :do_backup
echo FAIL_NO_BACKUP >> %LOG%
exit /b 1
:do_backup
call backup.bat >> %LOG% 2>&1
echo OK_BACKUP >> %LOG%
exit /b 0