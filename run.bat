@echo off
title Auto Clicker Pro Launcher
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo         ⚡ DANG KHOI DONG AUTO CLICKER PRO
echo ==================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python trong he thong!
    echo Vui long cai dat Python 3 va them vao PATH.
    pause
    exit /b
)

python main.py
if %errorlevel% neq 0 (
    echo.
    echo [THONG BAO] Ung dung da dung hoac xay ra loi.
    pause
)
