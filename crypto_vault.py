"""
Finding Token Encrypted License Vault.
Provides military-grade AES-256-GCM encryption and authenticated decryption
for the cloud subscription registry (finding_token_vault.bin) and local hardware-locked
license storage (license.dat).
Prevents any plaintext license exposure on GitHub or web hosts.
"""
import hashlib
import json
import base64
from Cryptodome.Cipher import AES

VAULT_MAGIC = b"FTV1"
LOCAL_LICENSE_MAGIC = b"FTL1"
RELAY_PREFIX = "FTR1:"
VAULT_PASSPHRASE = b"FindingToken_Portfolio_Auth_Vault_Key_2026_Secure$v1.1#Antigravity"
VAULT_KEY = hashlib.sha256(VAULT_PASSPHRASE).digest()


def encrypt_vault(licenses_dict: dict) -> bytes:
    """
    Encrypts a licenses dictionary into binary ciphertext using AES-256-GCM.
    Output: MAGIC(4B) + NONCE(16B) + MAC_TAG(16B) + CIPHERTEXT
    """
    raw_payload = json.dumps(licenses_dict, ensure_ascii=False).encode("utf-8")
    cipher = AES.new(VAULT_KEY, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(raw_payload)
    return VAULT_MAGIC + cipher.nonce + tag + ciphertext


def decrypt_vault(vault_bytes: bytes) -> dict:
    """
    Decrypts and validates the encrypted binary vault.
    Raises ValueError if data is tampered, corrupted, or invalid.
    """
    if len(vault_bytes) < 36:
        raise ValueError("Encrypted vault payload is too short.")
    
    magic = vault_bytes[:4]
    if magic != VAULT_MAGIC:
        raise ValueError("Invalid vault header magic.")
    
    nonce = vault_bytes[4:20]
    tag = vault_bytes[20:36]
    ciphertext = vault_bytes[36:]
    
    cipher = AES.new(VAULT_KEY, AES.MODE_GCM, nonce=nonce)
    decrypted_bytes = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(decrypted_bytes.decode("utf-8"))


def encrypt_local_license(data_dict: dict, hwid: str) -> bytes:
    """
    Encrypts local license session dictionary with AES-256-GCM tied to the machine's HWID.
    Output: FTL1 + NONCE(16B) + TAG(16B) + CIPHERTEXT
    """
    key = hashlib.sha256(VAULT_PASSPHRASE + hwid.strip().upper().encode("utf-8")).digest()
    raw = json.dumps(data_dict, ensure_ascii=False).encode("utf-8")
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(raw)
    return LOCAL_LICENSE_MAGIC + cipher.nonce + tag + ciphertext


def decrypt_local_license(enc_bytes: bytes, hwid: str) -> dict:
    """
    Decrypts local license.dat tied to HWID.
    Raises ValueError if MAC verification fails, HWID is wrong, or payload is corrupted.
    """
    if len(enc_bytes) < 36:
        raise ValueError("Encrypted license payload too short.")
    if enc_bytes[:4] != LOCAL_LICENSE_MAGIC:
        raise ValueError("Invalid local license header magic.")
    
    key = hashlib.sha256(VAULT_PASSPHRASE + hwid.strip().upper().encode("utf-8")).digest()
    nonce = enc_bytes[4:20]
    tag = enc_bytes[20:36]
    ciphertext = enc_bytes[36:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    dec = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(dec.decode("utf-8"))


def encrypt_relay_payload(payload_dict: dict) -> str:
    """
    Encrypts activation relay broadcast using military-grade AES-256-GCM.
    Returns: FTR1:<base64_ciphertext>
    Guarantees NO plain text keys, HWIDs, or client names ever travel over public relays or GitHub.
    """
    raw = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")
    cipher = AES.new(VAULT_KEY, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(raw)
    combined = cipher.nonce + tag + ciphertext
    b64 = base64.b64encode(combined).decode("ascii")
    return f"{RELAY_PREFIX}{b64}"


def decrypt_relay_payload(payload_str: str) -> dict | None:
    """
    Decrypts relay payload. Supports both encrypted FTR1 format and legacy plain JSON.
    Returns decoded dictionary or None if invalid.
    """
    if not payload_str or not isinstance(payload_str, str):
        return None
    s = payload_str.strip()
    if s.startswith(RELAY_PREFIX):
        try:
            b64_part = s[len(RELAY_PREFIX):].strip()
            raw_bytes = base64.b64decode(b64_part)
            if len(raw_bytes) < 32:
                return None
            nonce = raw_bytes[:16]
            tag = raw_bytes[16:32]
            ciphertext = raw_bytes[32:]
            cipher = AES.new(VAULT_KEY, AES.MODE_GCM, nonce=nonce)
            dec = cipher.decrypt_and_verify(ciphertext, tag)
            return json.loads(dec.decode("utf-8"))
        except Exception:
            return None
    elif s.startswith("{"):
        try:
            return json.loads(s)
        except Exception:
            return None
    return None

