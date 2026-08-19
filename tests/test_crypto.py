"""Tests for password_manager.crypto module."""
import pytest

from password_manager.crypto import EncryptionError, EncryptionService


class TestEncryptionService:
    """Test cases for the EncryptionService class."""

    def test_generate_key_returns_bytes(self):
        """Test that generate_key returns a valid key as bytes."""
        crypto = EncryptionService()
        key = crypto.generate_key()

        assert isinstance(key, bytes)
        assert len(key) > 0

    def test_generate_key_produces_different_keys(self):
        """Test that multiple calls to generate_key produce different keys."""
        crypto = EncryptionService()
        key1 = crypto.generate_key()
        key2 = crypto.generate_key()

        assert key1 != key2

    def test_encrypt_with_generated_key(self):
        """Test encryption with an auto-generated key."""
        crypto = EncryptionService()
        plaintext = "secret message"

        key, ciphertext = crypto.encrypt(plaintext)

        assert isinstance(key, bytes)
        assert isinstance(ciphertext, bytes)
        assert key != plaintext.encode()
        assert ciphertext != plaintext.encode()

    def test_encrypt_with_provided_key(self):
        """Test encryption with a provided key."""
        crypto = EncryptionService()
        plaintext = "secret message"
        provided_key = crypto.generate_key()

        key, ciphertext = crypto.encrypt(plaintext, provided_key)

        assert key == provided_key

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        crypto = EncryptionService()

        key, ciphertext = crypto.encrypt("")

        assert isinstance(ciphertext, bytes)
        assert len(ciphertext) > 0

    def test_encrypt_special_characters(self):
        """Test encryption with special characters and unicode."""
        crypto = EncryptionService()
        plaintext = "p@ssw0rd!#$%&*()_±[]{}¶€€"

        key, ciphertext = crypto.encrypt(plaintext)

        assert crypto.decrypt(key, ciphertext) == plaintext

    def test_encrypt_non_string_raises_type_error(self):
        """Test that encrypting non-string raises TypeError."""
        crypto = EncryptionService()

        with pytest.raises(TypeError, match="plaintext must be a string"):
            crypto.encrypt(123)

        with pytest.raises(TypeError, match="plaintext must be a string"):
            crypto.encrypt(None)

        with pytest.raises(TypeError, match="plaintext must be a string"):
            crypto.encrypt(b"bytes")

    def test_decrypt_returns_original_plaintext(self):
        """Test that decrypting ciphertext returns the original plaintext."""
        crypto = EncryptionService()
        plaintext = "secret message"
        key, ciphertext = crypto.encrypt(plaintext)

        result = crypto.decrypt(key, ciphertext)

        assert result == plaintext

    def test_decrypt_with_wrong_key_raises_encryption_error(self):
        """Test that decrypting with wrong key raises EncryptionError."""
        crypto = EncryptionService()
        plaintext = "secret message"
        key, ciphertext = crypto.encrypt(plaintext)
        wrong_key = crypto.generate_key()

        with pytest.raises(EncryptionError, match="Unable to decrypt value"):
            crypto.decrypt(wrong_key, ciphertext)

    def test_decrypt_with_invalid_ciphertext_raises_encryption_error(self):
        """Test that decrypting invalid ciphertext raises EncryptionError."""
        crypto = EncryptionService()
        key = crypto.generate_key()
        invalid_ciphertext = b"not-valid-ciphertext"

        with pytest.raises(EncryptionError, match="Unable to decrypt value"):
            crypto.decrypt(key, invalid_ciphertext)

    def test_decrypt_with_invalid_key_format_raises_encryption_error(self):
        """Test that decrypting with invalid key format raises EncryptionError."""
        crypto = EncryptionService()
        plaintext = "secret message"
        _, ciphertext = crypto.encrypt(plaintext)
        invalid_key = b"not-a-valid-fernet-key"

        with pytest.raises(EncryptionError, match="Unable to decrypt value"):
            crypto.decrypt(invalid_key, ciphertext)

    def test_encrypt_and_decrypt_roundtrip(self):
        """Test complete encrypt-decrypt roundtrip with various inputs."""
        crypto = EncryptionService()
        plaintexts = [
            "simple password",
            "",
            "Pass123!@#",
            "Very long password with many characters and special symbols !@#$%^&*()",
            "🔐🔒🔑",  # Emoji
        ]

        for plaintext in plaintexts:
            key, ciphertext = crypto.encrypt(plaintext)
            decrypted = crypto.decrypt(key, ciphertext)
            assert decrypted == plaintext

    def test_encrypt_multiple_times_produces_different_ciphertexts(self):
        """Test that encrypting the same plaintext twice produces different ciphertexts."""
        crypto = EncryptionService()
        plaintext = "same message"
        key1, ciphertext1 = crypto.encrypt(plaintext)
        key2, ciphertext2 = crypto.encrypt(plaintext)

        # With auto-generated keys, the keys themselves will differ
        assert key1 != key2
        assert ciphertext1 != ciphertext2

    def test_encrypt_same_plaintext_with_same_key_produces_different_ciphertexts(self):
        """Test that Fernet timestamps cause different ciphertexts with same key."""
        crypto = EncryptionService()
        plaintext = "same message"
        key = crypto.generate_key()
        
        _, ciphertext1 = crypto.encrypt(plaintext, key)
        _, ciphertext2 = crypto.encrypt(plaintext, key)

        # Fernet includes timestamp, so ciphertexts should differ
        assert ciphertext1 != ciphertext2
        # But both should decrypt to same plaintext
        assert crypto.decrypt(key, ciphertext1) == plaintext
        assert crypto.decrypt(key, ciphertext2) == plaintext

    def test_large_plaintext_encryption_and_decryption(self):
        """Test encryption of large plaintext."""
        crypto = EncryptionService()
        large_plaintext = "x" * 100000  # 100KB of text

        key, ciphertext = crypto.encrypt(large_plaintext)
        decrypted = crypto.decrypt(key, ciphertext)

        assert decrypted == large_plaintext
