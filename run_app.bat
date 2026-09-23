@echo off
title MarkItDown Studio
cd /d "%~dp0"

:: 1. Detect Python and Pythonw commands
set PYTHON_CMD=
set PYTHONW_CMD=

python --version >nul 2>&1
if %errorlevel% equ 0 goto found_python

py --version >nul 2>&1
if %errorlevel% equ 0 goto found_py

goto no_python

:found_python
set PYTHON_CMD=python
goto resolve_pythonw

:found_py
set PYTHON_CMD=py
goto resolve_pythonw

:resolve_pythonw
pythonw --version >nul 2>&1
if %errorlevel% equ 0 goto set_pythonw

pyw --version >nul 2>&1
if %errorlevel% equ 0 goto set_pyw

:: Try to find pythonw from python directory
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys, os; print(os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'))"') do (
    if exist "%%i" (
        set PYTHONW_CMD="%%i"
        goto check_deps
    )
)

:: Fallback if pythonw is not found
set PYTHONW_CMD=%PYTHON_CMD%
goto check_deps

:set_pythonw
set PYTHONW_CMD=pythonw
goto check_deps

:set_pyw
set PYTHONW_CMD=pyw
goto check_deps

:no_python
echo ====================================================
echo             MarkItDown Studio
echo ====================================================
echo.
echo [ERROR] Python was not found in your system PATH.
echo.
echo Please install Python 3.10 or higher from:
echo https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:check_deps
:: 2. Pre-flight dependency check (silent if already satisfied)
%PYTHON_CMD% -c "import flask, markitdown, mammoth, openpyxl, pdfplumber" >nul 2>&1
if %errorlevel% equ 0 goto launch_background

echo ====================================================
echo             MarkItDown Studio
echo ====================================================
echo.
echo [INFO] Installing required dependencies...
if exist requirements.txt (
    %PYTHON_CMD% -m pip install -r requirements.txt
) else (
    %PYTHON_CMD% -m pip install flask "markitdown[all]" openai
)
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install required dependencies.
    pause
    exit /b 1
)

:launch_background
:: 3. Launch the app silently in background with pythonw and close terminal immediately
start "" %PYTHONW_CMD% app.py
exit
