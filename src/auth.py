"""
LOOPIEST KEYFINDER - Authentication & Passkey Engine.
Implements a 5-tier cryptographic and mathematical sequence validation system
for offline, zero-database active passkey verification.
"""

import os
import re
import hashlib
import random
import string
from typing import Tuple, Dict, List, Optional

# Alphanumeric character set for passkey blocks
PASSKEY_CHARS = string.ascii_uppercase + string.digits

# Prime weight coefficients for polynomial checksum (12 characters: B1 + B2 + B3)
PRIME_WEIGHTS = [3, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]

# Internal cryptographic salt for payload signature
AUTH_SALT = "LOOPIEST-KEYFINDER-V1-SIG"

import sys

# Passkey regex pattern: LPST-XXXX-XXXX-XXXX-XXXX
PASSKEY_REGEX = re.compile(r"^LPST-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}$")

# Default license file name saved in software root folder on C:
LICENSE_FILENAME = "license.key"
ALT_LICENSE_FILENAMES = ["license.key", "license.txt", ".license"]


def get_app_root_dir() -> str:
    """
    Returns the absolute path to the software root folder on C:.
    Works both in development mode and compiled standalone executable (.exe).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    # Sub-regra B1: Soma ASCII % 13 == 5
    if sum(ord(c) for c in b1) % 13 != 5:
        return False, "Falha na congruência modular do Bloco 1.", checks

    # Sub-regra B2: Paridade alternada (0+2 par, 1+3 ímpar)
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
    """
    Generates a single valid passkey that strictly satisfies all 5 verification layers.
    """
    inv_w11 = pow(PRIME_WEIGHTS[11], -1, 97)

    while True:
        # 1. Generate B1 satisfying sum % 13 == 5
        b1_prefix = [random.choice(PASSKEY_CHARS) for _ in range(3)]
        rem = (5 - sum(ord(c) for c in b1_prefix)) % 13
        valid_b1_4 = [c for c in PASSKEY_CHARS if ord(c) % 13 == rem]
        if not valid_b1_4:
            continue
        b1 = "".join(b1_prefix) + random.choice(valid_b1_4)

        # 2. Generate B2 satisfying cross-parity rules
        b2_0 = random.choice(PASSKEY_CHARS)
        valid_b2_2 = [c for c in PASSKEY_CHARS if (ord(c) + ord(b2_0)) % 2 == 0]
        b2_2 = random.choice(valid_b2_2)

        b2_1 = random.choice(PASSKEY_CHARS)
        valid_b2_3 = [c for c in PASSKEY_CHARS if (ord(c) + ord(b2_1)) % 2 == 1]
        b2_3 = random.choice(valid_b2_3)

        b2 = b2_0 + b2_1 + b2_2 + b2_3

        # 3. Generate B3 satisfying weighted sum % 97 == 42
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

        # 4. Generate B4 using SHA-256 payload signature
        payload = f"{b1}-{b2}-{b3}:{AUTH_SALT}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()
        b4 = digest[:2] + digest[-2:]

        candidate_key = f"LPST-{b1}-{b2}-{b3}-{b4}"

        # 5. Filter through Master Hash condition
        master_hash = hashlib.sha256(candidate_key.encode("utf-8")).hexdigest()
        if int(master_hash[:4], 16) % 11 == 0:
            return candidate_key


def generate_passkeys(count: int = 500) -> List[str]:
    """
    Generates a specified number of unique, valid passkeys.
    """
    keys = set()
    while len(keys) < count:
        key = generate_single_passkey()
        # Double check validity
        valid, _, _ = validate_passkey(key)
        if valid:
            keys.add(key)
    return sorted(list(keys))


def ensure_pass_file(filepath: str = "pass.txt", count: int = 500) -> str:
    """
    Ensures that pass.txt exists with at least `count` valid keys.
    If the file does not exist or has fewer keys, it generates them.
    """
    need_generation = True
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            if len(lines) >= count:
                need_generation = False
        except Exception:
            need_generation = True

    if need_generation:
        keys = generate_passkeys(count)
        with open(filepath, "w", encoding="utf-8") as f:
            for key in keys:
                f.write(f"{key}\n")
        print(f"[LOOPIEST AUTH] {len(keys)} passkeys ativas salvas em: {filepath}")

    return filepath


def get_saved_passkey(base_dir: Optional[str] = None) -> Optional[str]:
    """
    Retrieves a previously saved passkey if valid from software root on C:.
    Checks license.key first, then fallback files.
    """
    if base_dir is None:
        base_dir = get_app_root_dir()

    for filename in ALT_LICENSE_FILENAMES:
        license_path = os.path.join(base_dir, filename)
        if os.path.exists(license_path):
            try:
                with open(license_path, "r", encoding="utf-8") as f:
                    key = f.read().strip()
                is_valid, _, _ = validate_passkey(key)
                if is_valid:
                    return key
            except Exception:
                pass
    return None


def save_passkey(key: str, base_dir: Optional[str] = None) -> bool:
    """
    Saves an active passkey to license.key in the software root directory on C:.
    """
    if base_dir is None:
        base_dir = get_app_root_dir()
    license_path = os.path.join(base_dir, LICENSE_FILENAME)

    try:
        with open(license_path, "w", encoding="utf-8") as f:
            f.write(key.strip().upper() + "\n")
        print(f"[LOOPIEST AUTH] Passkey ativa salva em: {license_path}")
        return True
    except Exception as err:
        print(f"[LOOPIEST AUTH] Erro ao salvar passkey ({err}).")
        return False


def clear_saved_passkey(base_dir: Optional[str] = None) -> bool:
    """
    Removes license files from software root directory.
    """
    if base_dir is None:
        base_dir = get_app_root_dir()

    cleared = False
    for filename in ALT_LICENSE_FILENAMES:
        license_path = os.path.join(base_dir, filename)
        if os.path.exists(license_path):
            try:
                os.remove(license_path)
                cleared = True
            except Exception:
                pass
    return cleared


USER_FILENAME = "user.txt"


def get_saved_username(base_dir: Optional[str] = None) -> Optional[str]:
    """
    Retrieves a registered username from user.txt in the software root directory on C:.
    """
    if base_dir is None:
        base_dir = get_app_root_dir()
    user_path = os.path.join(base_dir, USER_FILENAME)

    if os.path.exists(user_path):
        try:
            with open(user_path, "r", encoding="utf-8") as f:
                user = f.read().strip()
            if user:
                return user
        except Exception:
            pass
    return None


def save_username(username: str, base_dir: Optional[str] = None) -> bool:
    """
    Saves a username to user.txt in the software root directory on C:.
    """
    if base_dir is None:
        base_dir = get_app_root_dir()
    user_path = os.path.join(base_dir, USER_FILENAME)

    clean_user = username.strip()
    if not clean_user:
        return False

    try:
        with open(user_path, "w", encoding="utf-8") as f:
            f.write(clean_user + "\n")
        print(f"[LOOPIEST AUTH] Nome de usuário salvo em: {user_path}")
        return True
    except Exception as err:
        print(f"[LOOPIEST AUTH] Erro ao salvar nome de usuário ({err}).")
        return False


def clear_saved_username(base_dir: Optional[str] = None) -> bool:
    """
    Removes user.txt from software root directory.
    """
    if base_dir is None:
        base_dir = get_app_root_dir()
    user_path = os.path.join(base_dir, USER_FILENAME)

    if os.path.exists(user_path):
        try:
            os.remove(user_path)
            return True
        except Exception:
            pass
    return False

