@echo off
setlocal

cd /d "%~dp0"

set "OUT=dist"

echo === Building mitol.exe (onefile, via .spec) ===
call .venv\Scripts\activate
pyinstaller mitol.spec --noconfirm
if errorlevel 1 (
    echo.
    echo === BUILD FAILED ===
    exit /b 1
)

echo === Copying runtime files next to the exe ===
if exist schema_db.sql (
    copy /Y schema_db.sql "%OUT%\schema_db.sql" >nul
)
if exist icon.png (
    copy /Y icon.png "%OUT%\icon.png" >nul
)
if exist on.png (
    copy /Y on.png "%OUT%\on.png" >nul
)
if exist off.png (
    copy /Y off.png "%OUT%\off.png" >nul
)
if exist VERSION (
    copy /Y VERSION "%OUT%\VERSION" >nul
)

echo.
echo === Done. Exe: %OUT%\mitol.exe ===
echo === Ship the whole "%OUT%" folder, not just the exe. ===

endlocal
