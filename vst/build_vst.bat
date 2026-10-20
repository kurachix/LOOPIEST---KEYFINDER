@echo off
setlocal enabledelayedexpansion

echo =========================================================
echo   LOOPIEST KEYFINDER - SCRIPT DE COMPILACAO VST (FL STUDIO)
echo   Desenvolvido por @L8PIEST
echo =========================================================
echo.

where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [Status] Executando pipeline automatizado de compilacao VST...
    python "%~dp0build_vst_auto.py"
    if %errorlevel% equ 0 (
        echo.
        echo [OK] Compilacao e instalacao concluidas com sucesso!
        pause
        exit /b 0
    )
)

echo [Fallback] Tentando compilar via CMake...
where cmake >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] CMake nao encontrado.
    pause
    exit /b 1
)

cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel

pause
