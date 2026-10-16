@echo off
title Build AutoClicker C# Native
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo   🔨 DANG BIEN DICH AUTOCLICKER C# (.NET 10)
echo ==================================================
echo.

where dotnet >nul 2>nul
if %errorlevel% neq 0 (
    echo [LOI] May chua cai dat .NET SDK!
    pause
    exit /b
)

dotnet publish src_csharp\AutoClickerPro.csproj -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -o .
if %errorlevel% equ 0 (
    if exist "AutoClickerPro.exe" (
        copy /y "AutoClickerPro.exe" "AutoClicker.exe" >nul
        del "AutoClickerPro.exe" >nul 2>nul
    )
    echo.
    echo ==================================================
    echo   ✓ BIEN DICH THANH CONG! File AutoClicker.exe da san sang.
    echo ==================================================
) else (
    echo.
    echo [LOI] Bien dich that bai!
)
pause
