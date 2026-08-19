"""Tests for password_manager.repositories module - VaultRepositories class."""
import tempfile
from pathlib import Path

import pytest

from password_manager.models import DatabasePair
from password_manager.repositories import VaultRepositories


class TestVaultRepositories:
    """Test cases for the VaultRepositories class."""

    def test_vault_repositories_initialization(self, tmp_path):
        """Test VaultRepositories initialization."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            assert repo.keys is not None
            assert repo.hashes is not None
        finally:
            repo.close()

    def test_vault_repositories_initializes_both_databases(self, tmp_path):
        """Test that both databases are initialized."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            # Check that tables exist in both databases
            cursor = repo.keys.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            assert cursor.fetchone() is not None

            cursor = repo.hashes.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            assert cursor.fetchone() is not None
        finally:
            repo.close()

    def test_vault_repositories_close_closes_both(self, tmp_path):
        """Test that close() closes both repositories."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)
        repo.close()

        # Both connections should be closed
        import sqlite3
        with pytest.raises(sqlite3.ProgrammingError):
            repo.keys.connection.execute("SELECT 1")
        with pytest.raises(sqlite3.ProgrammingError):
            repo.hashes.connection.execute("SELECT 1")

    def test_vault_repositories_add_user_to_both(self, tmp_path):
        """Test adding user to both repositories."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            keys_id = repo.keys.add_user("alice", b"keys_master")
            hash_id = repo.hashes.add_user("alice", b"hashes_master")

            assert keys_id == 1
            assert hash_id == 1
        finally:
            repo.close()

    def test_vault_repositories_add_and_find_credentials(self, tmp_path):
        """Test adding and finding credentials using vault repositories."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            # Setup user
            user_id = repo.keys.add_user("alice", b"master_key")
            repo.hashes.add_user("alice", b"master_hash")

            # Add credential
            repo.hashes.add_credential(user_id, "example.com", "alice", b"encrypted", "note")
            repo.keys.add_key(user_id, "example.com", "alice", b"cred_key")

            # Find credential
            hash_results = repo.hashes.find_exact(user_id, "example.com", "alice")
            key_results = repo.keys.find_key(user_id, "example.com", "alice")

            assert len(hash_results) == 1
            assert len(key_results) == 1
            assert hash_results[0][4] == b"encrypted"
            assert key_results[0][4] == b"cred_key"
        finally:
            repo.close()

    def test_vault_repositories_update_credential(self, tmp_path):
        """Test updating credential in both repositories."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            user_id = repo.keys.add_user("alice", b"master_key")
            repo.hashes.add_user("alice", b"master_hash")

            repo.hashes.add_credential(user_id, "example.com", "alice", b"old_pass", "note")
            repo.keys.add_key(user_id, "example.com", "alice", b"old_key")

            # Update both
            repo.hashes.update_credential(
                user_id, "example.com", "alice", b"new_pass", "new note"
            )
            repo.keys.update_key(user_id, "example.com", "alice", b"new_key")

            hash_results = repo.hashes.find_exact(user_id, "example.com", "alice")
            key_results = repo.keys.find_key(user_id, "example.com", "alice")

            assert hash_results[0][4] == b"new_pass"
            assert key_results[0][4] == b"new_key"
        finally:
            repo.close()

    def test_vault_repositories_delete_credential(self, tmp_path):
        """Test deleting credential from both repositories."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            user_id = repo.keys.add_user("alice", b"master_key")
            repo.hashes.add_user("alice", b"master_hash")

            repo.hashes.add_credential(user_id, "example.com", "alice", b"pass", "note")
            repo.keys.add_key(user_id, "example.com", "alice", b"key")

            # Delete from both
            repo.hashes.delete_credential(user_id, "example.com", "alice")
            repo.keys.delete_key(user_id, "example.com", "alice")

            hash_results = repo.hashes.find_exact(user_id, "example.com", "alice")
            key_results = repo.keys.find_key(user_id, "example.com", "alice")

            assert hash_results == []
            assert key_results == []
        finally:
            repo.close()

    def test_vault_repositories_list_operations(self, tmp_path):
        """Test listing operations on both repositories."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            user_id = repo.keys.add_user("alice", b"master_key")
            repo.hashes.add_user("alice", b"master_hash")

            # Add multiple credentials
            for i in range(3):
                app = f"app{i}.com"
                repo.hashes.add_credential(user_id, app, "alice", b"pass", f"note{i}")
                repo.keys.add_key(user_id, app, "alice", b"key")

            # List from both repositories
            hash_list = repo.hashes.list_credentials(user_id)
            key_list = repo.keys.list_keys(user_id)

            assert len(hash_list) == 3
            assert len(key_list) == 3
        finally:
            repo.close()

    def test_vault_repositories_change_master_password(self, tmp_path):
        """Test changing master password in both repositories."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            user_id = repo.keys.add_user("alice", b"old_key")
            repo.hashes.add_user("alice", b"old_hash")

            # Change password in both
            repo.keys.update_user_password(user_id, b"new_key")
            repo.hashes.update_user_password(user_id, b"new_hash")

            key_results = repo.keys.find_user(user_id=user_id)
            hash_results = repo.hashes.find_user(user_id=user_id)

            assert key_results[0][2] == b"new_key"
            assert hash_results[0][2] == b"new_hash"
        finally:
            repo.close()

    def test_vault_repositories_multiple_users(self, tmp_path):
        """Test vault repositories with multiple users."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            user1_id = repo.keys.add_user("alice", b"key1")
            user2_id = repo.keys.add_user("bob", b"key2")

            repo.hashes.add_user("alice", b"hash1")
            repo.hashes.add_user("bob", b"hash2")

            # Add credentials for each user
            repo.hashes.add_credential(user1_id, "example.com", "alice", b"pass1", "")
            repo.keys.add_key(user1_id, "example.com", "alice", b"key1")

            repo.hashes.add_credential(user2_id, "example.com", "bob", b"pass2", "")
            repo.keys.add_key(user2_id, "example.com", "bob", b"key2")

            # Verify isolation
            alice_creds = repo.hashes.list_credentials(user1_id)
            bob_creds = repo.hashes.list_credentials(user2_id)

            assert len(alice_creds) == 1
            assert len(bob_creds) == 1
            assert alice_creds[0][3] == "alice"
            assert bob_creds[0][3] == "bob"
        finally:
            repo.close()

    def test_vault_repositories_find_operations(self, tmp_path):
        """Test various find operations across repositories."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            user_id = repo.keys.add_user("alice", b"master_key")
            repo.hashes.add_user("alice", b"master_hash")

            # Add multiple credentials
            repo.hashes.add_credential(user_id, "example.com", "alice", b"pass1", "")
            repo.keys.add_key(user_id, "example.com", "alice", b"key1")

            repo.hashes.add_credential(user_id, "example.com", "bob", b"pass2", "")
            repo.keys.add_key(user_id, "example.com", "bob", b"key2")

            # Test partial search
            hash_results = repo.hashes.find_credentials(user_id, "example.com", "alice")
            assert len(hash_results) == 1
            assert hash_results[0][3] == "alice"
        finally:
            repo.close()

    def test_vault_repositories_concurrent_operations(self, tmp_path):
        """Test concurrent operations on different users."""
        databases = DatabasePair(
            keys_path=str(tmp_path / "keys.db"),
            hash_path=str(tmp_path / "hash.db"),
        )
        repo = VaultRepositories(databases)

        try:
            # Add two users with different credentials
            user1_id = repo.keys.add_user("alice", b"key1")
            repo.hashes.add_user("alice", b"hash1")

            user2_id = repo.keys.add_user("bob", b"key2")
            repo.hashes.add_user("bob", b"hash2")

            # Interleave operations
            repo.hashes.add_credential(user1_id, "app1.com", "alice", b"p1", "")
            repo.keys.add_key(user1_id, "app1.com", "alice", b"k1")

            repo.hashes.add_credential(user2_id, "app2.com", "bob", b"p2", "")
            repo.keys.add_key(user2_id, "app2.com", "bob", b"k2")

            repo.hashes.add_credential(user1_id, "app3.com", "alice", b"p3", "")
            repo.keys.add_key(user1_id, "app3.com", "alice", b"k3")

            # Verify correctness
            alice_list = repo.hashes.list_credentials(user1_id)
            bob_list = repo.hashes.list_credentials(user2_id)

            assert len(alice_list) == 2
            assert len(bob_list) == 1
        finally:
            repo.close()
