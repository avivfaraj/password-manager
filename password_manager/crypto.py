from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(Exception):
    """Exception raised when encryption or decryption fails."""


class EncryptionService:
    """Provide symmetric encryption helpers for app secrets and keys.

    Methods
    -------
    generate_key
        Create a new Fernet-compatible encryption key.
    encrypt
        Encrypt a string and optionally reuse a supplied key.
    decrypt
        Decrypt an encrypted payload into its original string.
    """

    def generate_key(self) -> bytes:
        """Generate a fresh Fernet-compatible encryption key.

        Returns
        -------
        bytes
            Random encryption key suitable for Fernet operations.
        """
        return Fernet.generate_key()

    def encrypt(self, plaintext: str, key: bytes | None = None) -> tuple[bytes, bytes]:
        """Encrypt a plaintext string.

        Parameters
        ----------
        plaintext : str
            String to encrypt.
        key : bytes, optional
            Existing encryption key to use. If not provided, a new key is generated.

        Returns
        -------
        tuple[bytes, bytes]
            The encryption key and the encrypted payload.

        Raises
        ------
        TypeError
            If ``plaintext`` is not a string.
        EncryptionError
            If a cryptographic error prevents encryption.
        """
        if not isinstance(plaintext, str):
            raise TypeError("plaintext must be a string")
        encryption_key = key or self.generate_key()
        try:
            return encryption_key, Fernet(encryption_key).encrypt(
                plaintext.encode("utf-8")
            )
        except Exception as exc:
            raise EncryptionError("Unable to encrypt value") from exc

    def decrypt(self, key: bytes, ciphertext: bytes) -> str:
        """Decrypt ciphertext using the provided key.

        Parameters
        ----------
        key : bytes
            Fernet key used to decrypt the payload.
        ciphertext : bytes
            Encrypted value to decode.

        Returns
        -------
        str
            Decrypted plaintext string.

        Raises
        ------
        EncryptionError
            If the payload is invalid, the key is invalid, or decryption fails.
        """
        try:
            return Fernet(key).decrypt(ciphertext).decode("utf-8")
        except (InvalidToken, ValueError, TypeError) as exc:
            raise EncryptionError("Unable to decrypt value") from exc
