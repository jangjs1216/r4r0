import os
import base64
import hashlib
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

def get_fernet_key() -> bytes:
    """
    Generate a 32-byte Base64 url-safe compatible key from the MASTER_KEY env var.
    If MASTER_KEY is not set, a warning is printed and a default insecure key is used (DEV ONLY).
    """
    master = os.getenv("MASTER_KEY")
    if not master:
        print("[WARNING] MASTER_KEY not set. Using insecure default key.")
        master = "insecure_default_master_key_do_not_use_in_prod"
    
    # Hash the master key to get stable 32 bytes
    digest = hashlib.sha256(master.encode()).digest()
    return base64.urlsafe_b64encode(digest)

_CIPHER_SUITE = None

def get_cipher():
    global _CIPHER_SUITE
    if _CIPHER_SUITE is None:
        key = get_fernet_key()
        _CIPHER_SUITE = Fernet(key)
    return _CIPHER_SUITE

def encrypt_secret(plain_text: str) -> bytes:
    if not plain_text:
        return b""
    cipher = get_cipher()
    return cipher.encrypt(plain_text.encode())

def decrypt_secret(cipher_text: bytes) -> str:
    if not cipher_text:
        return ""
    cipher = get_cipher()
    return cipher.decrypt(cipher_text).decode()
