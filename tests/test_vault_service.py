"""Tests for password_manager.services module - VaultService class."""
import tempfile
from pathlib import Path

import pytest

from password_manager.crypto import EncryptionService
from password_manager.models import Credential, DatabasePair
from password_manager.repositories import VaultRepositories
from password_manager.services import (
    AuthenticationService,
    CredentialNotFoundError,
    DuplicateCredentialError,
    VaultService,
)


class TestVaultService:
    """Test cases for the VaultService class."""

    @pytest.fixture
    def vault_setup(self, tmp_path):
        """Setup vault service with authenticated user."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)
        vault = VaultService(repositories, crypto)

        # Register a user
        user_id = auth.register("testuser", "master_password")

        yield vault, repositories, crypto, user_id

        repositories.close()

    def test_vault_service_initialization(self, tmp_path):
        """Test VaultService initialization."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        vault = VaultService(repositories, crypto)

        try:
            assert vault.repositories == repositories
            assert vault.crypto == crypto
        finally:
            repositories.close()

    def test_vault_service_add_credential_success(self, vault_setup):
        """Test adding a credential."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "secret_password", "Work account")

        # Verify it was stored
        cred = vault.get(user_id, "example.com", "alice")
        assert cred.application == "example.com"
        assert cred.username == "alice"
        assert cred.password == "secret_password"
        assert cred.comment == "Work account"

    def test_vault_service_add_credential_empty_application_raises_error(self, vault_setup):
        """Test that empty application raises ValueError."""
        vault, repositories, crypto, user_id = vault_setup

        with pytest.raises(ValueError, match="Application, username and password are required"):
            vault.add(user_id, "", "alice", "password", "note")

    def test_vault_service_add_credential_empty_username_raises_error(self, vault_setup):
        """Test that empty username raises ValueError."""
        vault, repositories, crypto, user_id = vault_setup

        with pytest.raises(ValueError, match="Application, username and password are required"):
            vault.add(user_id, "example.com", "", "password", "note")

    def test_vault_service_add_credential_empty_password_raises_error(self, vault_setup):
        """Test that empty password raises ValueError."""
        vault, repositories, crypto, user_id = vault_setup

        with pytest.raises(ValueError, match="Application, username and password are required"):
            vault.add(user_id, "example.com", "alice", "", "note")

    def test_vault_service_add_credential_duplicate_raises_error(self, vault_setup):
        """Test that adding duplicate credential raises error."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "password1", "note")

        with pytest.raises(DuplicateCredentialError, match="That credential already exists"):
            vault.add(user_id, "example.com", "alice", "password2", "note")

    def test_vault_service_get_credential_success(self, vault_setup):
        """Test retrieving a credential."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "secret_password", "Work account")

        cred = vault.get(user_id, "example.com", "alice")

        assert isinstance(cred, Credential)
        assert cred.application == "example.com"
        assert cred.username == "alice"
        assert cred.password == "secret_password"
        assert cred.comment == "Work account"

    def test_vault_service_get_credential_not_found_raises_error(self, vault_setup):
        """Test that getting non-existent credential raises error."""
        vault, repositories, crypto, user_id = vault_setup

        with pytest.raises(CredentialNotFoundError, match="Credential not found"):
            vault.get(user_id, "nonexistent.com", "alice")

    def test_vault_service_list_credentials(self, vault_setup):
        """Test listing all credentials for a user."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "pass1", "note1")
        vault.add(user_id, "other.com", "bob", "pass2", "note2")
        vault.add(user_id, "example.org", "alice", "pass3", "note3")

        credentials = vault.list(user_id)

        assert len(credentials) == 3
        assert all(isinstance(c, Credential) for c in credentials)
        assert [c.application for c in credentials] == ["example.com", "other.com", "example.org"]

    def test_vault_service_list_empty_vault(self, vault_setup):
        """Test listing credentials from empty vault."""
        vault, repositories, crypto, user_id = vault_setup

        credentials = vault.list(user_id)

        assert credentials == []

    def test_vault_service_search_by_application(self, vault_setup):
        """Test searching credentials by application."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "pass1", "")
        vault.add(user_id, "example.com", "bob", "pass2", "")
        vault.add(user_id, "other.com", "alice", "pass3", "")

        results = vault.search(user_id, "example.com", "")

        assert len(results) == 2
        assert all(c.application == "example.com" for c in results)

    def test_vault_service_search_by_application_and_username(self, vault_setup):
        """Test searching credentials by application and username."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "pass1", "")
        vault.add(user_id, "example.com", "alice.admin", "pass2", "")
        vault.add(user_id, "example.com", "bob", "pass3", "")

        results = vault.search(user_id, "example.com", "alice")

        assert len(results) == 2
        assert all("alice" in c.username for c in results)

    def test_vault_service_search_partial_matching(self, vault_setup):
        """Test that search uses prefix matching."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "pass1", "")
        vault.add(user_id, "example.org", "alice", "pass2", "")
        vault.add(user_id, "example.net", "alice", "pass3", "")

        results = vault.search(user_id, "example.", "")

        assert len(results) == 3

    def test_vault_service_search_no_matches(self, vault_setup):
        """Test searching with no matches."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "pass1", "")

        results = vault.search(user_id, "nonexistent", "")

        assert results == []

    def test_vault_service_update_credential_password_and_comment(self, vault_setup):
        """Test updating credential password and comment."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "old_password", "old note")

        vault.update(user_id, "example.com", "alice", "new_password", "new note", True)

        cred = vault.get(user_id, "example.com", "alice")
        assert cred.password == "new_password"
        assert cred.comment == "new note"

    def test_vault_service_update_credential_comment_only(self, vault_setup):
        """Test updating only the comment."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "password", "old note")

        vault.update(user_id, "example.com", "alice", "new_password", "new note", False)

        cred = vault.get(user_id, "example.com", "alice")
        assert cred.password == "password"  # Password unchanged
        assert cred.comment == "new note"

    def test_vault_service_update_credential_not_found_raises_error(self, vault_setup):
        """Test that updating non-existent credential raises error."""
        vault, repositories, crypto, user_id = vault_setup

        with pytest.raises(CredentialNotFoundError, match="Credential not found"):
            vault.update(user_id, "nonexistent.com", "alice", "password", "note", True)

    def test_vault_service_delete_credential(self, vault_setup):
        """Test deleting a credential."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "password", "note")
        vault.delete(user_id, "example.com", "alice")

        with pytest.raises(CredentialNotFoundError):
            vault.get(user_id, "example.com", "alice")

    def test_vault_service_delete_credential_not_found_raises_error(self, vault_setup):
        """Test that deleting non-existent credential raises error."""
        vault, repositories, crypto, user_id = vault_setup

        with pytest.raises(CredentialNotFoundError, match="Credential not found"):
            vault.delete(user_id, "nonexistent.com", "alice")

    def test_vault_service_delete_one_credential_preserves_others(self, vault_setup):
        """Test that deleting one credential doesn't affect others."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "pass1", "")
        vault.add(user_id, "example.com", "bob", "pass2", "")

        vault.delete(user_id, "example.com", "alice")

        credentials = vault.list(user_id)
        assert len(credentials) == 1
        assert credentials[0].username == "bob"

    def test_vault_service_multiple_users_isolated(self, tmp_path):
        """Test that multiple users' credentials are isolated."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repositories = VaultRepositories(databases)
        crypto = EncryptionService()
        auth = AuthenticationService(repositories, crypto)
        vault = VaultService(repositories, crypto)

        try:
            alice_id = auth.register("alice", "alice_pass")
            bob_id = auth.register("bob", "bob_pass")

            vault.add(alice_id, "example.com", "alice_user", "alice_cred", "")
            vault.add(bob_id, "example.com", "bob_user", "bob_cred", "")

            alice_creds = vault.list(alice_id)
            bob_creds = vault.list(bob_id)

            assert len(alice_creds) == 1
            assert len(bob_creds) == 1
            assert alice_creds[0].password == "alice_cred"
            assert bob_creds[0].password == "bob_cred"
        finally:
            repositories.close()

    def test_vault_service_credential_contains_timestamps(self, vault_setup):
        """Test that retrieved credentials have timestamps."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "password", "note")

        cred = vault.get(user_id, "example.com", "alice")

        assert cred.date_modified
        assert cred.time_modified
        assert "/" in cred.date_modified  # DD/MM/YYYY format
        assert ":" in cred.time_modified  # HH:MM:SS format

    def test_vault_service_add_update_delete_sequence(self, vault_setup):
        """Test complete sequence of add, update, delete."""
        vault, repositories, crypto, user_id = vault_setup

        # Add
        vault.add(user_id, "example.com", "alice", "pass1", "note1")
        assert len(vault.list(user_id)) == 1

        # Update
        vault.update(user_id, "example.com", "alice", "pass2", "note2", True)
        cred = vault.get(user_id, "example.com", "alice")
        assert cred.password == "pass2"

        # Delete
        vault.delete(user_id, "example.com", "alice")
        assert len(vault.list(user_id)) == 0

    def test_vault_service_special_characters_in_credential(self, vault_setup):
        """Test handling credentials with special characters."""
        vault, repositories, crypto, user_id = vault_setup

        special_app = "app-with_special.chars@123"
        special_user = "user!@#$%^&*()"
        special_pass = "p@ss@wörd!🔐€"
        special_comment = "Comment with 中文 and émojis 😀"

        vault.add(user_id, special_app, special_user, special_pass, special_comment)

        cred = vault.get(user_id, special_app, special_user)
        assert cred.application == special_app
        assert cred.username == special_user
        assert cred.password == special_pass
        assert cred.comment == special_comment

    def test_vault_service_large_number_of_credentials(self, vault_setup):
        """Test handling many credentials."""
        vault, repositories, crypto, user_id = vault_setup

        # Add 50 credentials
        for i in range(50):
            vault.add(user_id, f"app{i:03d}.com", f"user{i}", f"pass{i}", f"note{i}")

        credentials = vault.list(user_id)
        assert len(credentials) == 50

    def test_vault_service_search_case_sensitive(self, vault_setup):
        """Test that search is case-sensitive."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "Example.com", "Alice", "password", "")

        # Exact match should work
        cred = vault.get(user_id, "Example.com", "Alice")
        assert cred.username == "Alice"

        # Different case should not match in get
        with pytest.raises(CredentialNotFoundError):
            vault.get(user_id, "example.com", "alice")

    def test_vault_service_empty_comment_handling(self, vault_setup):
        """Test handling credentials with empty comments."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "password", "")

        cred = vault.get(user_id, "example.com", "alice")
        assert cred.comment == ""

    def test_vault_service_from_row_creates_credential_correctly(self, vault_setup):
        """Test that _from_row creates Credential objects correctly."""
        vault, repositories, crypto, user_id = vault_setup

        vault.add(user_id, "example.com", "alice", "password", "note")

        credentials = vault.list(user_id)
        cred = credentials[0]

        assert isinstance(cred, Credential)
        assert cred.application == "example.com"
        assert cred.username == "alice"
        assert cred.password == "password"
        assert cred.comment == "note"
