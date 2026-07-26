"""
==============================================================================
LOOPIEST KEYFINDER - SCRIPT AUTOMATIZADO DE DEVOPS & EMPACOTAMENTO DE SOFTWARE
==============================================================================
Este script automatiza 100% o processo de compilação e criação do instalador:
  1. Compilação do código Python para Executável (.exe) standalone via PyInstaller.
  2. Conversão e preparação automática de assets visuais (Ícone .ico / Imagens Wizard).
  3. Geração automática do script de instalação Inno Setup (.iss) com estilo Dark/Neon.
  4. Automação da compilação do Instalador Profissional Windows (Loopiest_Setup.exe).

------------------------------------------------------------------------------
FERRAMENTAS NECESSÁRIAS NA MÁQUINA DE DESENVOLVIMENTO (DEV):
------------------------------------------------------------------------------
1. Python 3.10+ com PySide6 (instalado no ambiente do projeto).
2. PyInstaller (instalado automaticamente via pip se ausente pelo script).
3. Inno Setup 6 (Gratuito): Baixar em https://jrsoftware.org/isdl.php
   - Localizado em 'C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe' ou adicionado ao PATH.
==============================================================================
"""

import os
import sys
import shutil
import subprocess
from typing import Optional


def preparar_assets_icones(base_dir: str):
    """
    Converte o arquivo logo.png para logo.ico e logo.bmp usando PySide6
    para garantir compatibilidade perfeita com o Inno Setup.
    """
    logo_png = os.path.join(base_dir, "assets", "logo.png")
    logo_ico = os.path.join(base_dir, "assets", "logo.ico")
    logo_bmp = os.path.join(base_dir, "assets", "logo.bmp")

    if not os.path.exists(logo_png):
        print("[Aviso Assets] logo.png não encontrado em assets/")
        return

    try:
        from PySide6.QtGui import QImage
        from PySide6.QtCore import Qt

        img = QImage(logo_png)
        if not img.isNull():
            if not os.path.exists(logo_ico):
                img_scaled_ico = img.scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_scaled_ico.save(logo_ico, "ICO")
                print("[OK] [Asset Generator] Ícone assets/logo.ico gerado com sucesso!")

            if not os.path.exists(logo_bmp):
                img_scaled_bmp = img.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_scaled_bmp.save(logo_bmp, "BMP")
                print("[OK] [Asset Generator] Imagem assets/logo.bmp gerada com sucesso!")
    except Exception as e:
        print(f"[Aviso Asset Generator] Não foi possível converter ícones automaticamente ({e}).")


def compilar_pyinstaller(base_dir: str):
    """
    Compila o código-fonte Python para uma pasta auto-contida via PyInstaller.
    Configura a flag --windowed / --noconsole para omitir o terminal do Windows.
    """
    print("\n---------------------------------------------------------")
    print("FASE 1: COMPILAÇÃO DO APLICATIVO STANDALONE (PyInstaller)")
    print("---------------------------------------------------------")

    main_script = os.path.join(base_dir, "main.py")
    logo_png = os.path.join(base_dir, "assets", "logo.png")
    logo_ico = os.path.join(base_dir, "assets", "logo.ico")

    # Verifica e instala PyInstaller caso não esteja instalado
    try:
        import PyInstaller
    except ImportError:
        print("[DevOps] PyInstaller não encontrado. Instalando via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",                       # Pasta auto-contida com dependências embutidas
        "--windowed",                     # Sem janela de console (noconsole)
        "--name=LOOPIEST_KEYFINDER",
        f"--add-data={os.path.join('assets', 'logo.png')};assets",
        f"--add-data={os.path.join('styles', 'theme.qss')};styles",
        # Explicit hidden imports to prevent missing dependency runtime crashes
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=librosa",
        "--hidden-import=soundfile",
        "--hidden-import=scipy",
        "--hidden-import=numpy",
        main_script
    ]

    if os.path.exists(logo_ico):
        cmd.insert(-1, f"--icon={logo_ico}")
    elif os.path.exists(logo_png):
        cmd.insert(-1, f"--icon={logo_png}")

    print("[Status] Executando compilação PyInstaller...")
    subprocess.check_call(cmd, cwd=base_dir)
    print("[OK] [PyInstaller] Compilação concluída com sucesso em dist/LOOPIEST_KEYFINDER/")


def gerar_script_inno_setup(base_dir: str) -> str:
    """
    Gera dinamicamente o arquivo de configuração de instalador Inno Setup (.iss)
    com visual Dark/Roxo Neon, créditos de desenvolvimento e checkboxes finais.
    """
    iss_file_path = os.path.join(base_dir, "installer.iss")

    logo_ico_path = "assets\\logo.ico" if os.path.exists(os.path.join(base_dir, "assets", "logo.ico")) else "assets\\logo.png"
    logo_bmp_path = "assets\\logo.bmp" if os.path.exists(os.path.join(base_dir, "assets", "logo.bmp")) else "assets\\logo.png"

    iss_content = f"""; ==============================================================================
; INNO SETUP SCRIPT - LOOPIEST KEYFINDER INSTALLER
; Desenvolvido por @kxrachi & @willalvxrez
; ==============================================================================

[Setup]
AppId={{8A2BE200-L8PI-KEYF-INDE-R00000000001}}
AppName=LOOPIEST KEYFINDER
AppVersion=1.0.0
AppPublisher=@kxrachi & @willalvxrez
AppPublisherURL=https://www.instagram.com/l8piest/
AppSupportURL=https://www.instagram.com/l8piest/
AppUpdatesURL=https://www.instagram.com/l8piest/
DefaultDirName={{autopf}}\\LOOPIEST KEYFINDER
DefaultGroupName=LOOPIEST KEYFINDER
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=Loopiest_Setup
SetupIconFile={logo_ico_path}
WizardSmallImageFile={logo_bmp_path}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Personalização Visual de Cores (Estética Dark Obsidian & Roxo Neon)
WizardColor=#0A0A0E
WizardImageAlphaFormat=defined

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho (Desktop)"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked
Name: "startmenuicon"; Description: "Adicionar ao Menu Iniciar"; GroupDescription: "Atalhos adicionais:"

[Files]
Source: "dist\\LOOPIEST_KEYFINDER\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\LOOPIEST KEYFINDER"; Filename: "{{app}}\\LOOPIEST_KEYFINDER.exe"; Tasks: startmenuicon
Name: "{{autodesktop}}\\LOOPIEST KEYFINDER"; Filename: "{{app}}\\LOOPIEST_KEYFINDER.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\LOOPIEST_KEYFINDER.exe"; Description: "Executar o LOOPIEST KEYFINDER agora"; Flags: nowait postinstall skipifsilent
Filename: "https://www.instagram.com/l8piest/"; Description: "Visitar o Instagram da Loopiest (@l8piest)"; Flags: shellexec postinstall unchecked

[Messages]
brazilianportuguese.FinishedHeadingLabel=Instalação Concluída com Sucesso!
brazilianportuguese.FinishedLabel=Obrigado pela compra do LOOPIEST KEYFINDER!%n%nSoftware e Loopiest desenvolvidos por @kxrachi e @willalvxrez.%n%nSelecione as opções abaixo para iniciar:
"""

    with open(iss_file_path, "w", encoding="utf-8") as f:
        f.write(iss_content)

    print("[OK] [Inno Setup Generator] Script installer.iss gerado com sucesso!")
    return iss_file_path


def localizar_inno_setup_compiler() -> Optional[str]:
    """
    Localiza o compilador Inno Setup (ISCC.exe) nos caminhos padrão do sistema ou PATH.
    """
    # 1. Procura no PATH do sistema
    iscc_path = shutil.which("iscc")
    if iscc_path:
        return iscc_path

    # 2. Caminhos padrão de instalação do Inno Setup no Windows
    caminhos_padrao = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]

    for caminho in caminhos_padrao:
        if os.path.exists(caminho):
            return caminho

    return None


def compilar_instalador_inno(iss_file_path: str):
    """
    Compila o script installer.iss executando o ISCC.exe para produzir Loopiest_Setup.exe.
    """
    print("\n---------------------------------------------------------")
    print("FASE 2: GERAÇÃO DO INSTALADOR PROFISSIONAL (Inno Setup)")
    print("---------------------------------------------------------")

    iscc_exe = localizar_inno_setup_compiler()

    if not iscc_exe:
        print("\n[Aviso Inno Setup] O compilador Inno Setup (ISCC.exe) não foi encontrado.")
        print("Para gerar o arquivo Loopiest_Setup.exe automaticamente:")
        print("  1. Baixe e instale o Inno Setup 6 gratuito em: https://jrsoftware.org/isdl.php")
        print("  2. Em seguida, execute este script novamente (python build.py) ou abra o installer.iss no Inno Setup GUI.\n")
        return

    print(f"[DevOps] Compilador Inno Setup localizado em: '{iscc_exe}'")
    print("[Status] Compilando instalador Loopiest_Setup.exe...")

    try:
        subprocess.check_call([iscc_exe, iss_file_path])
        output_setup = os.path.join(os.path.dirname(iss_file_path), "Output", "Loopiest_Setup.exe")
        print("\n=========================================================")
        print("🎉 INSTALADOR PROFISSIONAL GERADO COM SUCESSO!")
        print(f"📦 Arquivo Final: {output_setup}")
        print("=========================================================")
    except Exception as e:
        print(f"\n[Erro na compilação Inno Setup]: {e}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("=========================================================")
    print("  LOOPIEST KEYFINDER - AUTOMATED BUILD & SETUP SYSTEM")
    print("  Desenvolvido por @kxrachi & @willalvxrez")
    print("=========================================================")

    # 1. Preparar assets de ícones (.ico / .bmp)
    preparar_assets_icones(base_dir)

    # 2. Compilar aplicação via PyInstaller (Fase 1)
    compilar_pyinstaller(base_dir)

    # 3. Gerar script de instalação Inno Setup (.iss)
    iss_file = gerar_script_inno_setup(base_dir)

    # 4. Compilar Instalador (.exe) via Inno Setup (Fase 2)
    compilar_instalador_inno(iss_file)


if __name__ == "__main__":
    main()
