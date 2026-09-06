@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title LMTS 1.6 EXE Builder
cd /d "%~dp0"

if not exist "send.pyw" for /r "%~dp0" %%F in (send.pyw) do if not "%%~dpF"=="%~dp0" copy /y "%%F" "send.pyw" >nul
if not exist "display.pyw" for /r "%~dp0" %%F in (display.pyw) do if not "%%~dpF"=="%~dp0" copy /y "%%F" "display.pyw" >nul

echo ========================================
echo   LMTS 1.6 - Build Windows EXE files
echo ========================================
echo.

if not exist "send.pyw" goto :source_missing
if not exist "display.pyw" goto :source_missing

call :find_python
if not defined PYTHON_EXE goto :python_missing

if not exist "dist" mkdir "dist"
if not exist "dist" goto :directory_failed

set "SEND_OUTPUT=%CD%\dist\send.exe"
set "DISPLAY_OUTPUT=%CD%\dist\display.exe"
call :stop_and_remove_output "%SEND_OUTPUT%" "send"
if errorlevel 1 goto :output_locked
call :stop_and_remove_output "%DISPLAY_OUTPUT%" "display"
if errorlevel 1 goto :output_locked

echo [1/6] Removing old temporary build files...
if exist ".build-venv" rmdir /s /q ".build-venv"
if exist "build" rmdir /s /q "build"
if exist ".build-venv" goto :cleanup_failed
if exist "build" goto :cleanup_failed
mkdir "build\spec"
if not exist "build\spec" goto :directory_failed

echo [2/6] Creating an isolated Python build environment...
"%PYTHON_EXE%" -m venv ".build-venv"
if errorlevel 1 goto :venv_failed
set "BUILD_PY=%CD%\.build-venv\Scripts\python.exe"
if not exist "%BUILD_PY%" goto :venv_failed

echo [3/6] Installing PyInstaller from a domestic mirror...
set "PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn"
"%BUILD_PY%" -m pip install --disable-pip-version-check --upgrade pip pyinstaller
if errorlevel 1 (
    echo Tsinghua mirror failed. Trying the Aliyun mirror...
    "%BUILD_PY%" -m pip install --disable-pip-version-check --upgrade pip pyinstaller --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
)
if errorlevel 1 goto :dependency_failed

if exist "requirements.txt" (
    "%BUILD_PY%" -m pip install --disable-pip-version-check -r "requirements.txt"
    if errorlevel 1 goto :dependency_failed
)

echo [4/6] Building send.exe...
"%BUILD_PY%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --noupx ^
    --onefile ^
    --windowed ^
    --name send ^
    --distpath "%CD%\dist" ^
    --workpath "%CD%\build\send" ^
    --specpath "%CD%\build\spec" ^
    "%CD%\send.pyw"
if errorlevel 1 goto :send_failed
if not exist "dist\send.exe" goto :send_failed

echo [5/6] Building display.exe...
"%BUILD_PY%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --noupx ^
    --onefile ^
    --windowed ^
    --name display ^
    --distpath "%CD%\dist" ^
    --workpath "%CD%\build\display" ^
    --specpath "%CD%\build\spec" ^
    "%CD%\display.pyw"
if errorlevel 1 goto :display_failed
if not exist "dist\display.exe" goto :display_failed

echo [6/6] Copying configuration and removing temporary environment...
if exist "lmts_school.json" copy /y "lmts_school.json" "dist\lmts_school.json" >nul
if exist "allow_firewall.bat" copy /y "allow_firewall.bat" "dist\allow_firewall.bat" >nul
if exist "README_CN.txt" copy /y "README_CN.txt" "dist\README_CN.txt" >nul
if exist ".build-venv" rmdir /s /q ".build-venv"
if exist "build" rmdir /s /q "build"

echo.
echo ========================================
echo   BUILD SUCCESSFUL
echo   %CD%\dist\send.exe
echo   %CD%\dist\display.exe
echo ========================================
echo Run allow_firewall.bat once on BOTH computers.
echo If an EXE still fails, check send_error.log or display_error.log.
echo.
explorer "%CD%\dist" >nul 2>nul
pause
exit /b 0

:find_python
set "PYTHON_EXE="
for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
if defined PYTHON_EXE if exist "%PYTHON_EXE%" exit /b 0
for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
if defined PYTHON_EXE if exist "%PYTHON_EXE%" exit /b 0
set "PYTHON_EXE="
exit /b 0

:stop_and_remove_output
set "OUTPUT_FILE=%~f1"
set "PROCESS_NAME=%~2"
if not exist "%OUTPUT_FILE%" exit /b 0
echo Closing old %PROCESS_NAME%.exe from this project's dist folder...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$target=[IO.Path]::GetFullPath($env:OUTPUT_FILE); Get-Process -Name $env:PROCESS_NAME -ErrorAction SilentlyContinue ^| Where-Object { try { [IO.Path]::GetFullPath($_.Path) -ieq $target } catch { $false } } ^| Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>nul
for /l %%R in (1,1,5) do (
    del /f /q "%OUTPUT_FILE%" >nul 2>nul
    if not exist "%OUTPUT_FILE%" exit /b 0
    timeout /t 1 /nobreak >nul
)
exit /b 1

:source_missing
echo [ERROR] send.pyw or display.pyw is missing beside this BAT.
goto :failed

:python_missing
echo [ERROR] Python 3 was not found.
echo Run run_pyw.bat first; it can install Python automatically.
goto :failed

:output_locked
echo [ERROR] An old EXE is still running or locked by antivirus.
echo Close it and run this BAT again.
goto :failed

:cleanup_failed
echo [ERROR] The old .build-venv or build directory is locked.
goto :failed

:directory_failed
echo [ERROR] Failed to create a build/output directory.
goto :failed

:venv_failed
echo [ERROR] Failed to create the isolated build environment.
goto :failed

:dependency_failed
echo [ERROR] Failed to install PyInstaller.
goto :failed

:send_failed
echo [ERROR] send.exe build failed. Read the messages above.
goto :failed

:display_failed
echo [ERROR] display.exe build failed. Read the messages above.

:failed
echo Temporary files are kept after a failed build for diagnosis.
echo You can use run_pyw.bat to run the PYW files directly.
echo.
pause
exit /b 1

