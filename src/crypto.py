"""
LOOPIEST KEYFINDER - Cryptographic Vault Engine.
Implements authenticated binary encryption (PBKDF2-HMAC-SHA256 + CTR Keystream + HMAC Tag)
to store passkeys, licenses, and user profile data in encrypted binary format (.dat / .lpst).
"""

import os
import hmac
import hashlib
import secrets
from typing import Tuple, Optional

# Magic header for encrypted binary files
MAGIC_HEADER = b"LPST_ENC\x01"

# Internal vault master passphrase
VAULT_PASSPHRASE = b"LOOPIEST_AUTHENTICATOR_VAULT_KEY_2026_MASTER"


def _derive_keys(salt: bytes) -> Tuple[bytes, bytes]:
    """Derives a 32-byte encryption key and a 32-byte HMAC integrity key via PBKDF2."""
    master = hashlib.pbkdf2_hmac("sha256", VAULT_PASSPHRASE, salt, 40000, dklen=64)
    return master[:32], master[32:]


def encrypt_data(plaintext: bytes) -> bytes:
    """
    Encrypts plaintext bytes using a random 16-byte salt, 16-byte nonce,
    keystream cipher, and Encrypt-then-MAC authentication.
    """
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(16)
    enc_key, mac_key = _derive_keys(salt)

    # Generate keystream blocks via HMAC-SHA256 CTR
    keystream = bytearray()
    counter = 0
    while len(keystream) < len(plaintext):
        block = hmac.new(enc_key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        keystream.extend(block)
        counter += 1

    ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream[:len(plaintext)]))
    tag = hmac.new(mac_key, MAGIC_HEADER + salt + nonce + ciphertext, hashlib.sha256).digest()

    return MAGIC_HEADER + salt + nonce + ciphertext + tag


def decrypt_data(encrypted_data: bytes) -> bytes:
    """
    Decrypts and validates integrity of an encrypted binary file.
    Raises ValueError if corrupted or tampered.
    """
    min_len = len(MAGIC_HEADER) + 16 + 16 + 32
    if len(encrypted_data) < min_len:
        raise ValueError("Arquivo corrompido ou formato binário criptográfico inválido.")

    if not encrypted_data.startswith(MAGIC_HEADER):
        raise ValueError("Assinatura mágica do arquivo criptografado não reconhecida.")

    offset = len(MAGIC_HEADER)
    salt = encrypted_data[offset:offset + 16]
    nonce = encrypted_data[offset + 16:offset + 32]
    tag = encrypted_data[-32:]
    ciphertext = encrypted_data[offset + 32:-32]

    enc_key, mac_key = _derive_keys(salt)
    expected_tag = hmac.new(mac_key, MAGIC_HEADER + salt + nonce + ciphertext, hashlib.sha256).digest()

    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("Falha na validação de integridade: Chave ou arquivo criptografado violado.")

    keystream = bytearray()
    counter = 0
    while len(keystream) < len(ciphertext):
        block = hmac.new(enc_key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        keystream.extend(block)
        counter += 1

    return bytes(a ^ b for a, b in zip(ciphertext, keystream[:len(ciphertext)]))


def encrypt_file(input_path: str, output_path: str) -> bool:
    """Encrypts a source text/binary file and writes to output binary file."""
    try:
        with open(input_path, "rb") as f:
            data = f.read()
        encrypted = encrypt_data(data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(encrypted)
        return True
    except Exception as e:
        print(f"[Crypto Error] Falha ao criptografar {input_path}: {e}")
        return False


def decrypt_file(encrypted_path: str) -> Optional[bytes]:
    """Reads and decrypts an encrypted binary file, returning plaintext bytes."""
    try:
        if not os.path.exists(encrypted_path):
            return None
        with open(encrypted_path, "rb") as f:
            data = f.read()
        return decrypt_data(data)
    except Exception as e:
        print(f"[Crypto Error] Falha ao descriptografar {encrypted_path}: {e}")
        return None
