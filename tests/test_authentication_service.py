"""Tests for password_manager.services module - AuthenticationService class."""
import tempfile
from pathlib import Path

import pytest

from password_manager.crypto import EncryptionService
from password_manager.models import DatabasePair
from password_manager.repositories import VaultRepositories
from password_manager.services import AuthenticationError, AuthenticationService


class TestAuthenticationService:
    """Test cases for the AuthenticationService class."""

    def test_authentication_service_initialization(self, tmp_path):
        """Test AuthenticationService initialization."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            assert auth.repositories == repositories
            assert auth.crypto == crypto
        finally:
            repositories.close()

    def test_authentication_service_register_success(self, tmp_path):
        """Test successful user registration."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            user_id = auth.register("alice", "master_password")

            assert user_id == 1
            assert repositories.keys.find_user(username="alice")
            assert repositories.hashes.find_user(username="alice")
        finally:
            repositories.close()

    def test_authentication_service_register_empty_username_raises_error(self, tmp_path):
        """Test that empty username raises ValueError."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            with pytest.raises(ValueError, match="Username and password are required"):
                auth.register("", "master_password")
        finally:
            repositories.close()

    def test_authentication_service_register_empty_password_raises_error(self, tmp_path):
        """Test that empty password raises ValueError."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            with pytest.raises(ValueError, match="Username and password are required"):
                auth.register("alice", "")
        finally:
            repositories.close()

    def test_authentication_service_register_duplicate_username_raises_error(self, tmp_path):
        """Test that registering duplicate username raises AuthenticationError."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            auth.register("alice", "password1")

            with pytest.raises(AuthenticationError, match="Username already exists"):
                auth.register("alice", "password2")
        finally:
            repositories.close()

    def test_authentication_service_authenticate_success(self, tmp_path):
        """Test successful authentication."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            registered_id = auth.register("alice", "correct_password")
            authenticated_id = auth.authenticate("alice", "correct_password")

            assert authenticated_id == registered_id
        finally:
            repositories.close()

    def test_authentication_service_authenticate_wrong_password_raises_error(self, tmp_path):
        """Test that wrong password raises AuthenticationError."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            auth.register("alice", "correct_password")

            with pytest.raises(AuthenticationError, match="Username and/or password are incorrect"):
                auth.authenticate("alice", "wrong_password")
        finally:
            repositories.close()

    def test_authentication_service_authenticate_nonexistent_user_raises_error(self, tmp_path):
        """Test that authenticating non-existent user raises AuthenticationError."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            with pytest.raises(AuthenticationError, match="Username and/or password are incorrect"):
                auth.authenticate("nonexistent", "password")
        finally:
            repositories.close()

    def test_authentication_service_authenticate_case_sensitive_username(self, tmp_path):
        """Test that username matching is case-sensitive."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            auth.register("alice", "password")

            # Different case should fail
            with pytest.raises(AuthenticationError, match="Username and/or password are incorrect"):
                auth.authenticate("Alice", "password")
        finally:
            repositories.close()

    def test_authentication_service_change_master_password_success(self, tmp_path):
        """Test successfully changing master password."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            user_id = auth.register("alice", "old_password")
            auth.change_master_password(user_id, "old_password", "new_password")

            # Should authenticate with new password
            authenticated_id = auth.authenticate("alice", "new_password")
            assert authenticated_id == user_id

            # Should not authenticate with old password
            with pytest.raises(AuthenticationError):
                auth.authenticate("alice", "old_password")
        finally:
            repositories.close()

    def test_authentication_service_change_master_password_wrong_current_raises_error(self, tmp_path):
        """Test that wrong current password raises error."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            user_id = auth.register("alice", "correct_password")

            with pytest.raises(AuthenticationError, match="Invalid Password"):
                auth.change_master_password(user_id, "wrong_password", "new_password")
        finally:
            repositories.close()

    def test_authentication_service_change_master_password_nonexistent_user_raises_error(self, tmp_path):
        """Test that changing password for non-existent user raises error."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            with pytest.raises(AuthenticationError, match="User not found"):
                auth.change_master_password(999, "any_password", "new_password")
        finally:
            repositories.close()

    def test_authentication_service_master_password_returns_decrypted_password(self, tmp_path):
        """Test retrieving the master password for a user."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            original_password = "my_secret_master_password"
            user_id = auth.register("alice", original_password)

            retrieved_password = auth.master_password(user_id)

            assert retrieved_password == original_password
        finally:
            repositories.close()

    def test_authentication_service_master_password_nonexistent_user_raises_error(self, tmp_path):
        """Test that retrieving password for non-existent user raises error."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            with pytest.raises(AuthenticationError, match="User not found"):
                auth.master_password(999)
        finally:
            repositories.close()

    def test_authentication_service_multiple_users_isolated(self, tmp_path):
        """Test that multiple users are properly isolated."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            alice_id = auth.register("alice", "alice_password")
            bob_id = auth.register("bob", "bob_password")

            # Each user should authenticate only with their own password
            assert auth.authenticate("alice", "alice_password") == alice_id
            assert auth.authenticate("bob", "bob_password") == bob_id

            # Cross authentication should fail
            with pytest.raises(AuthenticationError):
                auth.authenticate("alice", "bob_password")

            with pytest.raises(AuthenticationError):
                auth.authenticate("bob", "alice_password")
        finally:
            repositories.close()

    def test_authentication_service_register_and_authenticate_sequence(self, tmp_path):
        """Test complete sequence of register and authenticate."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            # Register
            user_id1 = auth.register("user1", "password1")
            user_id2 = auth.register("user2", "password2")

            # Change password
            auth.change_master_password(user_id1, "password1", "new_password1")

            # Authenticate with new password
            auth_id = auth.authenticate("user1", "new_password1")
            assert auth_id == user_id1

            # Retrieve master password
            retrieved = auth.master_password(user_id1)
            assert retrieved == "new_password1"

            # user2's password unchanged
            assert auth.master_password(user_id2) == "password2"
        finally:
            repositories.close()

    def test_authentication_service_special_characters_in_password(self, tmp_path):
        """Test authentication with special characters in password."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            special_password = "p@ssw0rd!#$%&*()_±[]{}¶€"
            user_id = auth.register("alice", special_password)

            authenticated_id = auth.authenticate("alice", special_password)
            assert authenticated_id == user_id

            retrieved = auth.master_password(user_id)
            assert retrieved == special_password
        finally:
            repositories.close()

    def test_authentication_service_unicode_in_password(self, tmp_path):
        """Test authentication with unicode characters."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)

        try:
            unicode_password = "пароль密码🔐"
            user_id = auth.register("alice", unicode_password)

            authenticated_id = auth.authenticate("alice", unicode_password)
            assert authenticated_id == user_id
        finally:
            repositories.close()
