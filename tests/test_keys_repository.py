"""Tests for password_manager.repositories module - KeysRepository class."""
import tempfile
from pathlib import Path

import pytest

from password_manager.repositories import KeysRepository


class TestKeysRepository:
    """Test cases for the KeysRepository class."""

    def test_keys_repository_initialization(self, tmp_path):
        """Test KeysRepository initialization."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            assert repo.path == db_path
        finally:
            repo.close()

    def test_keys_repository_initialize_creates_tables(self, tmp_path):
        """Test that initialize() creates required tables."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()

            # Query system tables to verify user table exists
            cursor = repo.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            assert cursor.fetchone() is not None

            cursor = repo.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='list'"
            )
            assert cursor.fetchone() is not None
        finally:
            repo.close()

    def test_keys_repository_add_user_returns_id(self, tmp_path):
        """Test that add_user returns the user id."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"key123")

            assert isinstance(user_id, int)
            assert user_id > 0
        finally:
            repo.close()

    def test_keys_repository_add_user_incremental_ids(self, tmp_path):
        """Test that add_user generates incremental ids."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            id1 = repo.add_user("alice", b"key1")
            id2 = repo.add_user("bob", b"key2")
            id3 = repo.add_user("charlie", b"key3")

            assert id1 == 1
            assert id2 == 2
            assert id3 == 3
        finally:
            repo.close()

    def test_keys_repository_find_user_by_username(self, tmp_path):
        """Test finding user by username."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            repo.add_user("alice", b"key123")
            
            results = repo.find_user(username="alice")

            assert len(results) == 1
            assert results[0][1] == "alice"
            assert results[0][2] == b"key123"
        finally:
            repo.close()

    def test_keys_repository_find_user_by_user_id(self, tmp_path):
        """Test finding user by user_id."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            repo.add_user("alice", b"key123")
            
            results = repo.find_user(user_id=1)

            assert len(results) == 1
            assert results[0][0] == 1
            assert results[0][1] == "alice"
        finally:
            repo.close()

    def test_keys_repository_find_user_not_found(self, tmp_path):
        """Test finding non-existent user returns empty."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            
            results = repo.find_user(username="nonexistent")
            assert results == []

            results = repo.find_user(user_id=999)
            assert results == []
        finally:
            repo.close()

    def test_keys_repository_find_user_no_args_returns_empty(self, tmp_path):
        """Test find_user with no arguments returns empty."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            repo.add_user("alice", b"key123")
            
            results = repo.find_user()
            assert results == []
        finally:
            repo.close()

    def test_keys_repository_add_key(self, tmp_path):
        """Test adding a key for a credential."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_key")
            
            repo.add_key(user_id, "example.com", "alice", b"credential_key")
            
            # Verify by finding the key
            results = repo.find_key(user_id, "example.com", "alice")
            assert len(results) == 1
            assert results[0][4] == b"credential_key"
        finally:
            repo.close()

    def test_keys_repository_find_key_exact_match(self, tmp_path):
        """Test finding exact key by user_id, app, and username."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_key")
            repo.add_key(user_id, "example.com", "alice", b"key1")
            repo.add_key(user_id, "example.com", "bob", b"key2")
            repo.add_key(user_id, "other.com", "alice", b"key3")
            
            results = repo.find_key(user_id, "example.com", "alice")
            
            assert len(results) == 1
            assert results[0][4] == b"key1"
        finally:
            repo.close()

    def test_keys_repository_find_key_not_found(self, tmp_path):
        """Test finding non-existent key returns empty."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_key")
            
            results = repo.find_key(user_id, "nonexistent.com", "alice")
            assert results == []
        finally:
            repo.close()

    def test_keys_repository_update_key(self, tmp_path):
        """Test updating an existing key."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_key")
            repo.add_key(user_id, "example.com", "alice", b"old_key")
            
            repo.update_key(user_id, "example.com", "alice", b"new_key")
            
            results = repo.find_key(user_id, "example.com", "alice")
            assert results[0][4] == b"new_key"
        finally:
            repo.close()

    def test_keys_repository_delete_key(self, tmp_path):
        """Test deleting a key."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_key")
            repo.add_key(user_id, "example.com", "alice", b"key1")
            repo.add_key(user_id, "example.com", "bob", b"key2")
            
            repo.delete_key(user_id, "example.com", "alice")
            
            # Verify alice's key is gone
            results = repo.find_key(user_id, "example.com", "alice")
            assert results == []
            
            # Verify bob's key still exists
            results = repo.find_key(user_id, "example.com", "bob")
            assert len(results) == 1
        finally:
            repo.close()

    def test_keys_repository_update_user_password(self, tmp_path):
        """Test updating a user's master password."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"old_master_key")
            
            repo.update_user_password(user_id, b"new_master_key")
            
            results = repo.find_user(user_id=user_id)
            assert results[0][2] == b"new_master_key"
        finally:
            repo.close()

    def test_keys_repository_list_keys_returns_all_for_user(self, tmp_path):
        """Test listing all keys for a user."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user1_id = repo.add_user("alice", b"key1")
            user2_id = repo.add_user("bob", b"key2")
            
            repo.add_key(user1_id, "example.com", "alice", b"cred_key1")
            repo.add_key(user1_id, "other.com", "alice", b"cred_key2")
            repo.add_key(user2_id, "example.com", "bob", b"cred_key3")
            
            results = repo.list_keys(user1_id)
            
            assert len(results) == 2
            # Should be in insertion order
            assert results[0][2] == "example.com"
            assert results[1][2] == "other.com"
        finally:
            repo.close()

    def test_keys_repository_list_keys_empty_for_new_user(self, tmp_path):
        """Test listing keys for user with no keys."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"key")
            
            results = repo.list_keys(user_id)
            assert results == []
        finally:
            repo.close()

    def test_keys_repository_list_keys_insertion_order(self, tmp_path):
        """Test that list_keys returns keys in insertion order."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"key")
            
            apps = ["app3.com", "app1.com", "app2.com"]
            for app in apps:
                repo.add_key(user_id, app, "alice", f"key_{app}".encode())
            
            results = repo.list_keys(user_id)
            
            # Should maintain insertion order
            assert results[0][2] == "app3.com"
            assert results[1][2] == "app1.com"
            assert results[2][2] == "app2.com"
        finally:
            repo.close()

    def test_keys_repository_multiple_users_isolated(self, tmp_path):
        """Test that multiple users' keys don't interfere."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user1_id = repo.add_user("alice", b"key1")
            user2_id = repo.add_user("bob", b"key2")
            
            repo.add_key(user1_id, "example.com", "alice", b"alice_key")
            repo.add_key(user2_id, "example.com", "bob", b"bob_key")
            
            results1 = repo.find_key(user1_id, "example.com", "alice")
            results2 = repo.find_key(user2_id, "example.com", "bob")
            
            assert results1[0][4] == b"alice_key"
            assert results2[0][4] == b"bob_key"
        finally:
            repo.close()

    def test_keys_repository_duplicate_keys_same_user_multiple_apps(self, tmp_path):
        """Test that same username can have keys in multiple apps."""
        db_path = str(tmp_path / "keys.db")
        repo = KeysRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_key")
            
            # Same username for different apps
            repo.add_key(user_id, "example.com", "alice", b"key1")
            repo.add_key(user_id, "other.com", "alice", b"key2")
            
            results = repo.list_keys(user_id)
            assert len(results) == 2
        finally:
            repo.close()
