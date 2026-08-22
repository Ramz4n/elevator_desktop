@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

set "SRC=dist"
set "STAGE=%TEMP%\mitol_release_stage"
set "OUT=release"

rem --- Поднимаем patch-версию в VERSION (1.0.0 -> 1.0.1), чтобы не забыть
rem     это сделать руками -- иначе свежая сборка продолжает считать себя
rem     старой версией и приложение зацикливается на предложении обновиться.
if not exist VERSION (
    echo 1.0.0> VERSION
)
set /p CURVER=<VERSION
for /f "tokens=1,2,3 delims=." %%a in ("%CURVER%") do (
    set "VMAJOR=%%a"
    set "VMINOR=%%b"
    set "VPATCH=%%c"
)
set /a VPATCH=%VPATCH%+1
set "NEWVER=%VMAJOR%.%VMINOR%.%VPATCH%"
echo %NEWVER%> VERSION
echo === Версия поднята: %CURVER% -^> %NEWVER% ===

rem --- Пересобираем -- build.bat заодно скопирует уже поднятый VERSION
rem     в dist\, иначе в архиве могла бы остаться версия от прошлой сборки.
call build.bat
if errorlevel 1 (
    echo.
    echo === СБОРКА НЕ УДАЛАСЬ ===
    exit /b 1
)

if not exist "%SRC%\mitol.exe" (
    echo.
    echo === "%SRC%\mitol.exe" не найден после сборки ===
    exit /b 1
)

echo === Готовлю чистую копию для релиза (без config.json и mitol.lock) ===
if exist "%STAGE%" rmdir /S /Q "%STAGE%"
robocopy "%SRC%" "%STAGE%" /E /XF config.json mitol.lock >nul

if not exist "%OUT%" mkdir "%OUT%"
set "ZIP=%OUT%\mitol_v%NEWVER%.zip"
if exist "%ZIP%" del /Q "%ZIP%"

echo === Архивирую в %ZIP% ===
powershell -NoProfile -Command "Compress-Archive -Path '%STAGE%\*' -DestinationPath '%ZIP%'"
if errorlevel 1 (
    echo.
    echo === АРХИВАЦИЯ НЕ УДАЛАСЬ ===
    exit /b 1
)

rmdir /S /Q "%STAGE%"

echo.
echo === Готово: %ZIP% ===
echo === Проверь перед заливкой на GitHub: unzip и убедись, что там НЕТ config.json ===
echo.
echo === На GitHub (репозиторий Ramz4n/mitol_releases) -^> Releases -^> Draft a new release: ===
echo ===   тег:   v%NEWVER%           (или v%NEWVER%-force для обязательного) ===
echo ===   asset: %ZIP% ===

endlocal
