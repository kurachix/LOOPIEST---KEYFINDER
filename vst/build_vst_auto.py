"""
LOOPIEST KEYFINDER - Automated VST Build & Installation Script for FL Studio
Compiles C++20 VST2 & VST3 binaries and installs to system VST folders.
"""

import os
import sys
import shutil
import subprocess
import glob

def find_zig():
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    pattern = os.path.join(local_app_data, "Microsoft", "WinGet", "Packages", "**", "zig.exe")
    matches = glob.glob(pattern, recursive=True)
    if matches:
        return matches[0]
    
    # Try system PATH
    zig_path = shutil.which("zig")
    if zig_path:
        return zig_path

    return None

def main():
    print("=========================================================")
    print("  LOOPIEST KEYFINDER - COMPILAÇÃO VST PARA FL STUDIO")
    print("  Desenvolvido por @L8PIEST")
    print("=========================================================\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_file = os.path.join(base_dir, "src", "VstMain.cpp")

    if not os.path.exists(source_file):
        print(f"[ERRO] Arquivo fonte não encontrado: {source_file}")
        sys.exit(1)

    zig_exe = find_zig()
    if not zig_exe or not os.path.exists(zig_exe):
        print("[ERRO] Compilador Zig C++ não encontrado.")
        sys.exit(1)

    print(f"[OK] Compilador localizado: {zig_exe}")

    bin_dir = os.path.join(base_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    output_dll = os.path.join(bin_dir, "LOOPIEST KEYFINDER.dll")

    print("[1/3] Compilando VST nativo x86_64 em C++20 com otimização -O3...")
    cmd = [
        zig_exe, "c++",
        "-O3",
        "-shared",
        "-std=c++20",
        "-o", output_dll,
        source_file,
        "-lgdi32", "-luser32", "-lgdiplus", "-lshell32", "-lole32"
    ]

    ret = subprocess.call(cmd)
    if ret != 0:
        print("[ERRO] Falha na compilação do plugin VST.")
        sys.exit(ret)

    dll_size = os.path.getsize(output_dll)
    print(f"[OK] Binário compilado com sucesso: {output_dll} ({dll_size // 1024} KB)")

    # -------------------------------------------------------------
    # 2. Criar Estrutura Padrão Steinberg VST3 Bundle
    # -------------------------------------------------------------
    print("\n[2/3] Gerando pacote Steinberg VST3 Bundle...")
    vst3_bundle_dir = os.path.join(bin_dir, "LOOPIEST KEYFINDER.vst3", "Contents", "x86_64-win")
    os.makedirs(vst3_bundle_dir, exist_ok=True)
    vst3_binary = os.path.join(vst3_bundle_dir, "LOOPIEST KEYFINDER.vst3")
    shutil.copy2(output_dll, vst3_binary)
    print(f"[OK] VST3 Bundle gerado: {vst3_binary}")

    # Também copia para a pasta dist/
    dist_vst3 = os.path.join(os.path.dirname(base_dir), "dist", "VST3", "LOOPIEST KEYFINDER.vst3", "Contents", "x86_64-win")
    os.makedirs(dist_vst3, exist_ok=True)
    shutil.copy2(output_dll, os.path.join(dist_vst3, "LOOPIEST KEYFINDER.vst3"))

    dist_vst2 = os.path.join(os.path.dirname(base_dir), "dist", "VST2")
    os.makedirs(dist_vst2, exist_ok=True)
    shutil.copy2(output_dll, os.path.join(dist_vst2, "LOOPIEST KEYFINDER.dll"))

    # -------------------------------------------------------------
    # 3. Instalar nos Diretórios do Sistema para FL Studio
    # -------------------------------------------------------------
    print("\n[3/3] Instalando nos diretórios padrão de plugins do FL Studio...")
    common_files = os.environ.get("COMMONPROGRAMFILES", r"C:\Program Files\Common Files")
    
    # Instalar VST3
    system_vst3 = os.path.join(common_files, "VST3", "LOOPIEST KEYFINDER.vst3", "Contents", "x86_64-win")
    try:
        os.makedirs(system_vst3, exist_ok=True)
        shutil.copy2(output_dll, os.path.join(system_vst3, "LOOPIEST KEYFINDER.vst3"))
        print(f"[OK] [VST3] Instalado com sucesso em: {system_vst3}")
    except Exception as e:
        print(f"[Aviso VST3] Permissão necessária para copiar para Common Files ({e}). Use a pasta dist/ se necessário.")

    # Instalar VST2 em VST2 e VstPlugins
    for vst2_folder in [os.path.join(common_files, "VST2"), r"C:\Program Files\VstPlugins"]:
        try:
            os.makedirs(vst2_folder, exist_ok=True)
            shutil.copy2(output_dll, os.path.join(vst2_folder, "LOOPIEST KEYFINDER.dll"))
            print(f"[OK] [VST2] Instalado com sucesso em: {vst2_folder}")
        except Exception:
            pass

    print("\n=========================================================")
    print("  BUILD E INSTALAÇÃO CONCLUÍDOS COM SUCESSO!")
    print("  O plugin já está compilado e pronto para o FL Studio!")
    print("=========================================================")

if __name__ == "__main__":
    main()
