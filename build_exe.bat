@echo off
title MarkItDown Studio Installer Compiler
echo ==============================================
echo  MarkItDown StudioStandalone EXE Compiler
echo ==============================================
echo.
cd /d "%~dp0"

echo [1/3] Ensuring PyInstaller is installed...
pip install pyinstaller

echo.
echo [2/3] Resolving magika asset directory...
for /f "delims=" %%i in ('python -c "import magika, os; print(os.path.dirname(magika.__file__))"') do set MAGIKA_DIR=%%i
echo Magika found at: %MAGIKA_DIR%

echo.
echo [3/3] Compiling application into a single executable...
echo This may take a few minutes as it packages python, markitdown,
echo openai, and all GUI renderers into a single standalone binary.
echo.

:: Clean previous build directory and spec file to prevent PyInstaller caching issues
if exist build rd /s /q build
if exist MarkItDownStudio.spec del MarkItDownStudio.spec

python -m PyInstaller --clean --noconsole --onefile --add-data "ui;ui" --add-data "%MAGIKA_DIR%\models;magika/models" --add-data "%MAGIKA_DIR%\config;magika/config" --name MarkItDownStudio app.py

if %errorlevel% equ 0 (
    echo.
    echo ==============================================
    echo  SUCCESS! Standalone application created!
    echo  Location: %~dp0dist\MarkItDownStudio.exe
    echo ==============================================
    echo.
) else (
    echo.
    echo ==============================================
    echo  ERROR: Compilation failed!
    echo ==============================================
    echo.
)
pause
