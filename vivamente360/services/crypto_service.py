from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
from django.conf import settings


class CryptoService:
    def __init__(self):
        key_b64 = settings.ENCRYPTION_KEY
        if isinstance(key_b64, str):
            self.key = base64.b64decode(key_b64)
        else:
            self.key = key_b64
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
