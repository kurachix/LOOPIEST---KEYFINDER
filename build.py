"""
==============================================================================
LOOPIEST KEYFINDER - SCRIPT AUTOMATIZADO DE DEVOPS & EMPACOTAMENTO DE SOFTWARE
==============================================================================
Este script automatiza 100% o processo de compilação e criação do instalador:
  1. Utiliza assets separados:
     - logo.png (Transparente) -> Interface do aplicativo (Splash & MainWindow)
     - installer_logo.jpg -> Ícones do Instalador Inno Setup (.exe / Wizard)
  2. Compilação do código Python para Executável (.exe) standalone via PyInstaller.
  3. Geração automática do script de instalação Inno Setup (.iss).
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
    Converte a imagem installer_logo.jpg para installer_logo.ico e installer_logo.bmp
    exclusivamente para uso no Inno Setup do Instalador.
    """
    installer_jpg = os.path.join(base_dir, "assets", "installer_logo.jpg")

    if not os.path.exists(installer_jpg):
        print("[Aviso Assets] installer_logo.jpg não encontrado em assets/")
        return

    installer_ico = os.path.join(base_dir, "assets", "installer_logo.ico")
    installer_bmp = os.path.join(base_dir, "assets", "installer_logo.bmp")

    try:
        from PySide6.QtGui import QImage
        from PySide6.QtCore import Qt

        img = QImage(installer_jpg)
        if not img.isNull():
            img_scaled_ico = img.scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            img_scaled_ico.save(installer_ico, "ICO")
            print("[OK] [Asset Generator] Ícone assets/installer_logo.ico atualizado!")

            img_scaled_bmp = img.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            img_scaled_bmp.save(installer_bmp, "BMP")
            print("[OK] [Asset Generator] Imagem assets/installer_logo.bmp atualizada!")
    except Exception as e:
        print(f"[Aviso Asset Generator] Não foi possível converter ícones do instalador automaticamente ({e}).")


def compilar_pyinstaller(base_dir: str):
    """
    Compila a aplicação mantendo a logo.png transparente para a UI do aplicativo.
    """
    print("\n---------------------------------------------------------")
    print("FASE 1: COMPILAÇÃO DO APLICATIVO STANDALONE (PyInstaller)")
    print("---------------------------------------------------------")

    main_script = os.path.join(base_dir, "main.py")
    logo_png = os.path.join(base_dir, "assets", "logo.png")
    installer_ico = os.path.join(base_dir, "assets", "installer_logo.ico")

    try:
        import PyInstaller
    except ImportError:
        print("[DevOps] PyInstaller não encontrado. Instalando via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=LOOPIEST_KEYFINDER",
        f"--add-data={logo_png};assets",
        f"--add-data={os.path.join('styles', 'theme.qss')};styles",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=librosa",
        "--hidden-import=soundfile",
        "--hidden-import=scipy",
        "--hidden-import=numpy",
        main_script
    ]

    if os.path.exists(installer_ico):
        cmd.insert(-1, f"--icon={installer_ico}")

    print("[Status] Executando compilação PyInstaller...")
    subprocess.check_call(cmd, cwd=base_dir)

    # Copia o ícone transparente para a pasta de distribuição
    dist_assets = os.path.join(base_dir, "dist", "LOOPIEST_KEYFINDER", "assets")
    os.makedirs(dist_assets, exist_ok=True)
    if os.path.exists(logo_png):
        shutil.copy(logo_png, os.path.join(dist_assets, "logo.png"))

    print("[OK] [PyInstaller] Compilação concluída com sucesso em dist/LOOPIEST_KEYFINDER/")


def gerar_script_inno_setup(base_dir: str) -> str:
    """
    Gera o script Inno Setup utilizando a logo escura (installer_logo) para os assistentes do instalador.
    """
    iss_file_path = os.path.join(base_dir, "installer.iss")

    installer_ico_path = "assets\\installer_logo.ico" if os.path.exists(os.path.join(base_dir, "assets", "installer_logo.ico")) else "assets\\installer_logo.jpg"
    installer_bmp_path = "assets\\installer_logo.bmp" if os.path.exists(os.path.join(base_dir, "assets", "installer_logo.bmp")) else "assets\\installer_logo.jpg"

    iss_content = f"""; ==============================================================================
; INNO SETUP SCRIPT - LOOPIEST KEYFINDER INSTALLER
; Desenvolvido por @kxrachi & @willalvxrez
; ==============================================================================

[Setup]
AppId={{{{8A2BE200-L8PI-KEYF-INDE-R00000000001}}}}
AppName=LOOPIEST KEYFINDER
AppVerName=LOOPIEST KEYFINDER
AppPublisher=@kxrachi & @willalvxrez
AppPublisherURL=https://www.instagram.com/l8piest/
AppSupportURL=https://www.instagram.com/l8piest/
AppUpdatesURL=https://www.instagram.com/l8piest/
DefaultDirName={{autopf}}\\LOOPIEST KEYFINDER
DefaultGroupName=LOOPIEST KEYFINDER
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=Loopiest_Setup
SetupIconFile={installer_ico_path}
WizardSmallImageFile={installer_bmp_path}
UninstallDisplayIcon={{app}}\\LOOPIEST_KEYFINDER.exe
UninstallDisplayName=LOOPIEST KEYFINDER
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho (Desktop)"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked
Name: "startmenuicon"; Description: "Adicionar ao Menu Iniciar"; GroupDescription: "Atalhos adicionais:"
Name: "taskbaricon"; Description: "Fixar na Barra de Tarefas (Taskbar)"; GroupDescription: "Atalhos adicionais:"

[Files]
Source: "dist\\LOOPIEST_KEYFINDER\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\LOOPIEST KEYFINDER"; Filename: "{{app}}\\LOOPIEST_KEYFINDER.exe"; Tasks: startmenuicon
Name: "{{autodesktop}}\\LOOPIEST KEYFINDER"; Filename: "{{app}}\\LOOPIEST_KEYFINDER.exe"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\User Pinned\\TaskBar\\LOOPIEST KEYFINDER"; Filename: "{{app}}\\LOOPIEST_KEYFINDER.exe"; Tasks: taskbaricon

[Run]
Filename: "{{app}}\\LOOPIEST_KEYFINDER.exe"; Description: "Executar o LOOPIEST KEYFINDER agora"; Flags: nowait postinstall skipifsilent
Filename: "https://www.instagram.com/l8piest/"; Flags: shellexec postinstall

[Messages]
brazilianportuguese.FinishedHeadingLabel=Instalação Concluída com Sucesso!
brazilianportuguese.FinishedLabel=Obrigado pela compra do LOOPIEST KEYFINDER!%n%nSoftware e Loopiest desenvolvidos por @kxrachi e @willalvxrez.
"""

    with open(iss_file_path, "w", encoding="utf-8") as f:
        f.write(iss_content)

    print("[OK] [Inno Setup Generator] Script installer.iss atualizado!")
    return iss_file_path


def localizar_inno_setup_compiler() -> Optional[str]:
    iscc_path = shutil.which("iscc")
    if iscc_path:
        return iscc_path

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
    print("\n---------------------------------------------------------")
    print("FASE 2: GERAÇÃO DO INSTALADOR PROFISSIONAL (Inno Setup)")
    print("---------------------------------------------------------")

    iscc_exe = localizar_inno_setup_compiler()

    if not iscc_exe:
        print("\n[Aviso Inno Setup] O compilador Inno Setup (ISCC.exe) não foi encontrado.")
        print(" Baixe em: https://jrsoftware.org/isdl.php e execute novamente python build.py.\n")
        return

    print(f"[DevOps] Compilador Inno Setup localizado em: '{iscc_exe}'")
    print("[Status] Compilando instalador Loopiest_Setup.exe...")

    try:
        subprocess.check_call([iscc_exe, iss_file_path])
        output_setup = os.path.join(os.path.dirname(iss_file_path), "Output", "Loopiest_Setup.exe")
        print("\n=========================================================")
        print("[SUCESSO] INSTALADOR PROFISSIONAL GERADO COM SUCESSO!")
        print(f"[OK] Arquivo Final: {output_setup}")
        print("=========================================================")
    except Exception as e:
        print(f"\n[Erro na compilação Inno Setup]: {e}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("=========================================================")
    print("  LOOPIEST KEYFINDER - AUTOMATED BUILD & SETUP SYSTEM")
    print("  Desenvolvido por @kxrachi & @willalvxrez")
    print("=========================================================")

    preparar_assets_icones(base_dir)
    compilar_pyinstaller(base_dir)
    iss_file = gerar_script_inno_setup(base_dir)
    compilar_instalador_inno(iss_file)


if __name__ == "__main__":
    main()
