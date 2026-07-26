"""
LOOPIEST KEYFINDER - Automatic Build & Executable Packaging Script.
Generates standalone distribution binaries using PyInstaller.
"""

import os
import sys
import subprocess


def build_executable():
    print("=========================================================")
    print("LOOPIEST KEYFINDER - Criador de Executável Distribuível")
    print("=========================================================\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(base_dir, "main.py")
    logo_path = os.path.join(base_dir, "assets", "logo.png")
    qss_path = os.path.join(base_dir, "styles", "theme.qss")

    # Install PyInstaller if missing
    try:
        import PyInstaller
    except ImportError:
        print("[Status] Instalando PyInstaller para empacotamento...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",             # Binário em pasta organizada para distribuição
        "--windowed",           # Ocultar janela de terminal/console
        "--name=LOOPIEST_KEYFINDER",
        f"--add-data={os.path.join('assets', 'logo.png')};assets",
        f"--add-data={os.path.join('styles', 'theme.qss')};styles",
        main_script
    ]

    if os.path.exists(logo_path):
        cmd.insert(-1, f"--icon={logo_path}")

    print("[Status] Compilando executável distribuível...")
    try:
        subprocess.check_call(cmd, cwd=base_dir)
        print("\n=========================================================")
        print("✔ SUCESSO: Executável gerado na pasta: dist/LOOPIEST_KEYFINDER/")
        print("=========================================================")
    except Exception as e:
        print(f"\n[Erro na compilação]: {e}")


if __name__ == "__main__":
    build_executable()
