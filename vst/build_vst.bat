@echo off
setlocal enabledelayedexpansion

echo =========================================================
echo   LOOPIEST KEYFINDER - SCRIPT DE COMPILACAO VST3 (FL STUDIO)
echo   Desenvolvido por @L8PIEST
echo =========================================================
echo.

where cmake >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] CMake nao foi encontrado no PATH do sistema.
    echo Baixe e instale o CMake em: https://cmake.org/download/
    echo Certifique-se de marcar a opcao "Add CMake to system PATH".
    pause
    exit /b 1
)

echo [1/3] Configurando ambiente de build via CMake...
cmake -B build -DCMAKE_BUILD_TYPE=Release
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao configurar projeto CMake.
    pause
    exit /b 1
)

echo.
echo [2/3] Compilando plugin VST3 e Standalone em C++20...
cmake --build build --config Release --parallel
if %errorlevel% neq 0 (
    echo [ERRO] Falha na compilacao C++.
    pause
    exit /b 1
)

echo.
echo [3/3] Instalando plugin na pasta do FL Studio...
set "VST3_DIR=%COMMONPROGRAMFILES%\VST3"
if not exist "!VST3_DIR!" mkdir "!VST3_DIR!"

if exist "build\LOOPIEST_KEYFINDER_artefacts\Release\VST3\LOOPIEST KEYFINDER.vst3" (
    xcopy /E /I /Y "build\LOOPIEST_KEYFINDER_artefacts\Release\VST3\LOOPIEST KEYFINDER.vst3" "!VST3_DIR!\LOOPIEST KEYFINDER.vst3"
    echo [SUCESSO] Plugin instalado em: !VST3_DIR!\LOOPIEST KEYFINDER.vst3
) else (
    echo [AVISO] Verifique a pasta build/LOOPIEST_KEYFINDER_artefacts/Release/VST3 para o arquivo .vst3 gerado.
)

echo.
echo =========================================================
echo   COMPILACAO E INSTALACAO CONCLUIDAS COM SUCESSO!
echo   No FL Studio:
echo   1. Va em Options ^> Manage Plugins
echo   2. Clique em "Find installed plugins"
echo   3. Adicione o LOOPIEST KEYFINDER no Mixer ou Master!
echo =========================================================
pause
