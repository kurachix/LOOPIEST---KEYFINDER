"""
LOOPIEST KEYFINDER - Utilitário de Exportação de Chaves.
Descriptografa o cofre C:\\loopiest\\acess\\pass.dat e exporta as 500 senhas em texto puro.
"""

from src.auth import export_passkeys_txt

if __name__ == "__main__":
    export_passkeys_txt("pass.txt")
