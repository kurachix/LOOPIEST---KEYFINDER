"""
LOOPIEST KEYFINDER - Authentication & Passkey Engine.
Implements a 5-tier cryptographic and mathematical sequence validation system
and encrypted binary storage (.dat) in C:\\loopiest\\acess.
"""

import os
import sys
import re
import hashlib
import random
import string
from typing import Tuple, Dict, List, Optional

from src.crypto import encrypt_data, decrypt_data, decrypt_file

# Alphanumeric character set for passkey blocks
PASSKEY_CHARS = string.ascii_uppercase + string.digits

# Prime weight coefficients for polynomial checksum (12 characters: B1 + B2 + B3)
PRIME_WEIGHTS = [3, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]

# Internal cryptographic salt for payload signature
AUTH_SALT = "LOOPIEST-KEYFINDER-V1-SIG"

# Passkey regex pattern: LPST-XXXX-XXXX-XXXX-XXXX
PASSKEY_REGEX = re.compile(r"^LPST-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}$")


def get_app_root_dir() -> str:
    """
    Returns the absolute path to the software root folder.
    Works both in development mode and compiled standalone executable (.exe).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_root_access_dir() -> str:
    """
    Returns the root access directory on the system drive: C:\\loopiest\\acess.
    Ensures directory exists with proper permissions.
    """
    system_drive = os.environ.get("SystemDrive", "C:")
    access_dir = os.path.join(system_drive + os.sep, "loopiest", "acess")
    try:
        os.makedirs(access_dir, exist_ok=True)
        return access_dir
    except Exception:
        fallback_dir = os.path.join(os.path.expanduser("~"), ".loopiest", "acess")
        os.makedirs(fallback_dir, exist_ok=True)
        return fallback_dir


def validate_passkey(key: str) -> Tuple[bool, str, Dict[str, bool]]:
    """
    Validates a passkey through 5 distinct sequence and cryptographic checks.
    
    Returns:
        (is_valid: bool, status_message: str, checks_status: Dict[str, bool])
    """
    checks = {
        "format": False,
        "modulo_parity": False,
        "weighted_checksum": False,
        "sha256_sig": False,
        "master_hash": False,
    }

    if not isinstance(key, str):
        return False, "Formato de chave inválido.", checks

    normalized_key = key.strip().upper()

    # --- VERIFICAÇÃO 1: Estrutura, Prefixo e Alfabeto ---
    if len(normalized_key) != 24:
        return False, "Comprimento incorreto (deve ter 24 caracteres).", checks

    if not PASSKEY_REGEX.match(normalized_key):
        return False, "Formato inválido. Padrão requerido: LPST-XXXX-XXXX-XXXX-XXXX", checks

    parts = normalized_key.split("-")
    if len(parts) != 5 or parts[0] != "LPST":
        return False, "Prefixo inválido (deve iniciar com LPST-).", checks

    b1, b2, b3, b4 = parts[1], parts[2], parts[3], parts[4]
    checks["format"] = True

    # --- VERIFICAÇÃO 2: Paridade Cruzada e Módulo dos Blocos Iniciais ---
    if sum(ord(c) for c in b1) % 13 != 5:
        return False, "Falha na congruência modular do Bloco 1.", checks

    if (ord(b2[0]) + ord(b2[2])) % 2 != 0:
        return False, "Falha na paridade de posições do Bloco 2.", checks

    if (ord(b2[1]) + ord(b2[3])) % 2 != 1:
        return False, "Falha na paridade alternada do Bloco 2.", checks

    checks["modulo_parity"] = True

    # --- VERIFICAÇÃO 3: Checksum Polinomial Ponderado Multibloco ---
    s12 = b1 + b2 + b3
    weighted_total = sum(ord(s12[i]) * PRIME_WEIGHTS[i] for i in range(12))
    if weighted_total % 97 != 42:
        return False, "Falha no checksum polinomial ponderado multibloco.", checks

    checks["weighted_checksum"] = True

    # --- VERIFICAÇÃO 4: Assinatura Criptográfica SHA-256 do Bloco 4 ---
    payload = f"{b1}-{b2}-{b3}:{AUTH_SALT}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()
    expected_b4 = digest[:2] + digest[-2:]

    if b4 != expected_b4:
        return False, "Assinatura criptográfica SHA-256 do Bloco 4 divergente.", checks

    checks["sha256_sig"] = True

    # --- VERIFICAÇÃO 5: Restrição de Dispersão do Master Hash ---
    master_hash = hashlib.sha256(normalized_key.encode("utf-8")).hexdigest()
    if int(master_hash[:4], 16) % 11 != 0:
        return False, "Falha no alinhamento do Master Hash de sequência.", checks

    checks["master_hash"] = True

    return True, "Passkey 100% válida e ativada com sucesso!", checks


def generate_single_passkey() -> str:
    """Generates a single valid passkey that strictly satisfies all 5 verification layers."""
    inv_w11 = pow(PRIME_WEIGHTS[11], -1, 97)

    while True:
        # 1. B1 satisfying sum % 13 == 5
        b1_prefix = [random.choice(PASSKEY_CHARS) for _ in range(3)]
        rem = (5 - sum(ord(c) for c in b1_prefix)) % 13
        valid_b1_4 = [c for c in PASSKEY_CHARS if ord(c) % 13 == rem]
        if not valid_b1_4:
            continue
        b1 = "".join(b1_prefix) + random.choice(valid_b1_4)

        # 2. B2 satisfying cross-parity rules
        b2_0 = random.choice(PASSKEY_CHARS)
        valid_b2_2 = [c for c in PASSKEY_CHARS if (ord(c) + ord(b2_0)) % 2 == 0]
        b2_2 = random.choice(valid_b2_2)

        b2_1 = random.choice(PASSKEY_CHARS)
        valid_b2_3 = [c for c in PASSKEY_CHARS if (ord(c) + ord(b2_1)) % 2 == 1]
        b2_3 = random.choice(valid_b2_3)

        b2 = b2_0 + b2_1 + b2_2 + b2_3

        # 3. B3 satisfying weighted sum % 97 == 42
        b3_prefix = [random.choice(PASSKEY_CHARS) for _ in range(3)]
        partial_sum = sum(
            ord(c) * PRIME_WEIGHTS[i]
            for i, c in enumerate(b1 + b2 + "".join(b3_prefix))
        )
        target_ord_mod = ((42 - partial_sum) * inv_w11) % 97
        valid_b3_4 = [c for c in PASSKEY_CHARS if (ord(c) % 97) == target_ord_mod]
        if not valid_b3_4:
            continue
        b3 = "".join(b3_prefix) + random.choice(valid_b3_4)

        # 4. B4 using SHA-256 payload signature
        payload = f"{b1}-{b2}-{b3}:{AUTH_SALT}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()
        b4 = digest[:2] + digest[-2:]

        candidate_key = f"LPST-{b1}-{b2}-{b3}-{b4}"

        # 5. Filter through Master Hash condition
        master_hash = hashlib.sha256(candidate_key.encode("utf-8")).hexdigest()
        if int(master_hash[:4], 16) % 11 == 0:
            return candidate_key


def generate_passkeys(count: int = 500) -> List[str]:
    """Generates a specified number of unique, valid passkeys."""
    keys = set()
    while len(keys) < count:
        key = generate_single_passkey()
        valid, _, _ = validate_passkey(key)
        if valid:
            keys.add(key)
    return sorted(list(keys))


# ==============================================================================
# Armazenamento Criptografado em C:\loopiest\acess
# ==============================================================================

VAULT_PASSKEYS_FILENAME = "pass.dat"
VAULT_USER_FILENAME = "user.dat"
VAULT_LICENSE_FILENAME = "license.dat"


def ensure_pass_vault(count: int = 500) -> str:
    """
    Garante a presença do arquivo criptografado pass.dat em C:\\loopiest\\acess.
    Se não existir, gera as chaves e criptografa em formato binário autenticado.
    """
    access_dir = get_root_access_dir()
    vault_path = os.path.join(access_dir, VAULT_PASSKEYS_FILENAME)

    # 1. Verifica se já existe um pass.dat válido
    if os.path.exists(vault_path):
        try:
            decrypted = decrypt_file(vault_path)
            if decrypted:
                lines = [l.strip() for l in decrypted.decode("utf-8").splitlines() if l.strip()]
                if len(lines) >= count:
                    return vault_path
        except Exception:
            pass

    # 2. Migração automática de pass.txt local, caso exista
    base_dir = get_app_root_dir()
    legacy_pass_txt = os.path.join(base_dir, "pass.txt")
    if os.path.exists(legacy_pass_txt):
        try:
            with open(legacy_pass_txt, "r", encoding="utf-8") as f:
                content = f.read()
            encrypted = encrypt_data(content.encode("utf-8"))
            with open(vault_path, "wb") as f:
                f.write(encrypted)
            print(f"[LOOPIEST VAULT] pass.txt migrado e criptografado para: {vault_path}")
            return vault_path
        except Exception:
            pass

    # 3. Geração e criptografia direta para pass.dat
    keys = generate_passkeys(count)
    content = "\n".join(keys) + "\n"
    encrypted = encrypt_data(content.encode("utf-8"))
    with open(vault_path, "wb") as f:
        f.write(encrypted)
    print(f"[LOOPIEST VAULT] {len(keys)} passkeys ativas criptografadas em: {vault_path}")

    return vault_path


def load_active_passkeys() -> List[str]:
    """Descriptografa e lê as passkeys ativas de C:\\loopiest\\acess\\pass.dat em memória."""
    access_dir = get_root_access_dir()
    vault_path = os.path.join(access_dir, VAULT_PASSKEYS_FILENAME)
    decrypted = decrypt_file(vault_path)
    if decrypted:
        return [l.strip() for l in decrypted.decode("utf-8").splitlines() if l.strip()]
    return []


def export_passkeys_txt(target_path: str = "pass.txt") -> bool:
    """Exporta as chaves criptografadas de pass.dat de volta para um arquivo .txt legível."""
    keys = load_active_passkeys()
    if keys:
        with open(target_path, "w", encoding="utf-8") as f:
            for k in keys:
                f.write(f"{k}\n")
        print(f"[LOOPIEST VAULT] {len(keys)} chaves exportadas com sucesso para: {target_path}")
        return True
    return False


def get_saved_passkey() -> Optional[str]:
    """Recupera a passkey ativa do arquivo criptografado license.dat em C:\\loopiest\\acess."""
    access_dir = get_root_access_dir()
    license_dat = os.path.join(access_dir, VAULT_LICENSE_FILENAME)

    if os.path.exists(license_dat):
        decrypted = decrypt_file(license_dat)
        if decrypted:
            try:
                key = decrypted.decode("utf-8").strip()
                is_valid, _, _ = validate_passkey(key)
                if is_valid:
                    return key
            except Exception:
                pass

    # Migração retrocompatível caso exista license.key antigo no diretório do app
    base_dir = get_app_root_dir()
    for legacy_name in ["license.key", ".license"]:
        legacy_path = os.path.join(base_dir, legacy_name)
        if os.path.exists(legacy_path):
            try:
                with open(legacy_path, "r", encoding="utf-8") as f:
                    key = f.read().strip()
                is_valid, _, _ = validate_passkey(key)
                if is_valid:
                    save_passkey(key)
                    try:
                        os.remove(legacy_path)
                    except Exception:
                        pass
                    return key
            except Exception:
                pass

    return None


def save_passkey(key: str) -> bool:
    """Criptografa e salva a passkey ativa em C:\\loopiest\\acess\\license.dat."""
    access_dir = get_root_access_dir()
    license_dat = os.path.join(access_dir, VAULT_LICENSE_FILENAME)

    try:
        data = key.strip().upper().encode("utf-8")
        encrypted = encrypt_data(data)
        with open(license_dat, "wb") as f:
            f.write(encrypted)
        print(f"[LOOPIEST VAULT] Passkey criptografada salva em: {license_dat}")
        return True
    except Exception as err:
        print(f"[LOOPIEST VAULT] Erro ao criptografar passkey ({err}).")
        return False


def clear_saved_passkey() -> bool:
    """Remove o arquivo criptografado license.dat de C:\\loopiest\\acess."""
    access_dir = get_root_access_dir()
    license_dat = os.path.join(access_dir, VAULT_LICENSE_FILENAME)
    if os.path.exists(license_dat):
        try:
            os.remove(license_dat)
            return True
        except Exception:
            return False
    return False


def get_saved_username() -> Optional[str]:
    """Recupera o nome do produtor do arquivo criptografado user.dat em C:\\loopiest\\acess."""
    access_dir = get_root_access_dir()
    user_dat = os.path.join(access_dir, VAULT_USER_FILENAME)

    if os.path.exists(user_dat):
        decrypted = decrypt_file(user_dat)
        if decrypted:
            try:
                user = decrypted.decode("utf-8").strip()
                if user:
                    return user
            except Exception:
                pass

    # Migração retrocompatível de user.txt antigo
    base_dir = get_app_root_dir()
    legacy_user_txt = os.path.join(base_dir, "user.txt")
    if os.path.exists(legacy_user_txt):
        try:
            with open(legacy_user_txt, "r", encoding="utf-8") as f:
                user = f.read().strip()
            if user:
                save_username(user)
                try:
                    os.remove(legacy_user_txt)
                except Exception:
                    pass
                return user
        except Exception:
            pass

    return None


def save_username(username: str) -> bool:
    """Criptografa e salva o nome de usuário em C:\\loopiest\\acess\\user.dat."""
    access_dir = get_root_access_dir()
    user_dat = os.path.join(access_dir, VAULT_USER_FILENAME)

    clean_user = username.strip()
    if not clean_user:
        return False

    try:
        encrypted = encrypt_data(clean_user.encode("utf-8"))
        with open(user_dat, "wb") as f:
            f.write(encrypted)
        print(f"[LOOPIEST VAULT] Usuário criptografado salvo em: {user_dat}")
        return True
    except Exception as err:
        print(f"[LOOPIEST VAULT] Erro ao criptografar usuário ({err}).")
        return False


def clear_saved_username() -> bool:
    """Remove user.dat de C:\\loopiest\\acess."""
    access_dir = get_root_access_dir()
    user_dat = os.path.join(access_dir, VAULT_USER_FILENAME)
    if os.path.exists(user_dat):
        try:
            os.remove(user_dat)
            return True
        except Exception:
            return False
    return False
