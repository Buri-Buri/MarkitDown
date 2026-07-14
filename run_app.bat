@echo off
title MarkItDown Studio Launcher
echo Launching MarkItDown Studio...
cd /d "%~dp0"
python app.py
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)
