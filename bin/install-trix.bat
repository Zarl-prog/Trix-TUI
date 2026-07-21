@echo off
title Trix IDE Installer

echo ============================================
echo   Trix IDE Installer
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/2] Installing trix-ide via pip...
pip install -U trix-ide
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

echo [2/2] Installation complete!
echo.
echo You can now run: trix
echo.
pause
