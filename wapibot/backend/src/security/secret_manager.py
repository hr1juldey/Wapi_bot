"""Secret manager for encrypting/decrypting .env.txt secrets.

Uses AES-256-GCM for encryption with random nonces per value.
"""

import os
import base64
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SecretManager:
    """Manages encryption/decryption of secrets in .env.txt"""

    def __init__(self, master_key_path: str = "./master.key"):
        """Initialize secret manager.

        Args:
            master_key_path: Path to AES-256 master key file
        """
        self.master_key_path = Path(master_key_path)
        self._key: bytes | None = None

    def _load_master_key(self) -> bytes:
        """Load AES-256 key from file.

        Returns:
            32-byte AES key

        Raises:
            FileNotFoundError: If master.key doesn't exist
        """
        if self._key is None:
            if not self.master_key_path.exists():
                raise FileNotFoundError(
                    f"Master key not found: {self.master_key_path}\n"
                    "Run: python scripts/setup_security.py"
                )
            self._key = self.master_key_path.read_bytes()
            if len(self._key) != 32:
                raise ValueError("Master key must be exactly 32 bytes (AES-256)")
        return self._key

    def encrypt_value(self, plaintext: str) -> str:
        """Encrypt a secret value.

        Args:
            plaintext: Secret value to encrypt

        Returns:
            Encrypted value in format: ENC[base64_encoded_data]
        """
        key = self._load_master_key()
        aesgcm = AESGCM(key)

        # Generate random 12-byte nonce
        nonce = os.urandom(12)

        # Encrypt plaintext
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)

        # Combine nonce + ciphertext and base64 encode
        blob = base64.b64encode(nonce + ciphertext).decode('utf-8')

        return f"ENC[{blob}]"

    def decrypt_value(self, encrypted: str) -> str:
        """Decrypt a secret value.

        Args:
            encrypted: Encrypted value (ENC[...]) or plaintext

        Returns:
            Decrypted plaintext value
        """
        # Backward compatible: if not encrypted, return as-is
        if not encrypted.startswith("ENC["):
            return encrypted

        # Extract base64 blob
        blob_b64 = encrypted[4:-1]  # Remove "ENC[" and "]"
        blob = base64.b64decode(blob_b64)

        # Split nonce and ciphertext
        nonce, ciphertext = blob[:12], blob[12:]

        # Decrypt
        key = self._load_master_key()
        aesgcm = AESGCM(key)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext_bytes.decode('utf-8')


# Global secret manager instance
secret_manager = SecretManager()
