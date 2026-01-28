from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
from django.conf import settings


class CryptoService:
    def __init__(self):
        key_b64 = settings.ENCRYPTION_KEY
        if isinstance(key_b64, str):
            try:
                self.key = base64.b64decode(key_b64)
            except Exception as e:
                raise ValueError(
                    f"Invalid ENCRYPTION_KEY in settings. The key must be a valid base64-encoded string. "
                    f"Generate a valid key with: python -c 'import base64, os; print(base64.b64encode(os.urandom(32)).decode())' "
                    f"Error: {str(e)}"
                )
        else:
            self.key = key_b64

        # Validate key length (must be 32 bytes for AES-256)
        if len(self.key) != 32:
            raise ValueError(
                f"Invalid ENCRYPTION_KEY length. Expected 32 bytes, got {len(self.key)} bytes. "
                f"Generate a valid key with: python -c 'import base64, os; print(base64.b64encode(os.urandom(32)).decode())'"
            )

        self.aesgcm = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ''
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()

    def decrypt(self, encrypted: str) -> str:
        if not encrypted:
            return ''
        data = base64.b64decode(encrypted)
        nonce, ciphertext = data[:12], data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode()
