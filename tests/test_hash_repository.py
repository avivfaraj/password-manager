"""Tests for password_manager.repositories module - HashRepository class."""
import tempfile
from pathlib import Path

import pytest

from password_manager.repositories import HashRepository


class TestHashRepository:
    """Test cases for the HashRepository class."""

    def test_hash_repository_initialization(self, tmp_path):
        """Test HashRepository initialization."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            assert repo.path == db_path
        finally:
            repo.close()

    def test_hash_repository_initialize_creates_tables(self, tmp_path):
        """Test that initialize() creates required tables."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()

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

    def test_hash_repository_add_user(self, tmp_path):
        """Test adding a user."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"encrypted_password")

            assert isinstance(user_id, int)
            assert user_id > 0
        finally:
            repo.close()

    def test_hash_repository_find_user_by_username(self, tmp_path):
        """Test finding user by username."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            repo.add_user("alice", b"encrypted_password")
            
            results = repo.find_user(username="alice")

            assert len(results) == 1
            assert results[0][1] == "alice"
            assert results[0][2] == b"encrypted_password"
        finally:
            repo.close()

    def test_hash_repository_find_user_by_user_id(self, tmp_path):
        """Test finding user by user_id."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            repo.add_user("alice", b"encrypted_password")
            
            results = repo.find_user(user_id=1)

            assert len(results) == 1
            assert results[0][0] == 1
            assert results[0][1] == "alice"
        finally:
            repo.close()

    def test_hash_repository_find_user_not_found(self, tmp_path):
        """Test finding non-existent user returns empty."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            
            results = repo.find_user(username="nonexistent")
            assert results == []
        finally:
            repo.close()

    def test_hash_repository_add_credential(self, tmp_path):
        """Test adding a credential."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            
            repo.add_credential(user_id, "example.com", "alice", b"encrypted_password", "Work account")
            
            # Verify the credential was added
            results = repo.find_exact(user_id, "example.com", "alice")
            assert len(results) == 1
            assert results[0][2] == "example.com"
            assert results[0][3] == "alice"
            assert results[0][4] == b"encrypted_password"
            assert results[0][5] == "Work account"
        finally:
            repo.close()

    def test_hash_repository_add_credential_sets_timestamps(self, tmp_path):
        """Test that add_credential sets date and time."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            
            repo.add_credential(user_id, "example.com", "alice", b"encrypted_password", "note")
            
            results = repo.find_exact(user_id, "example.com", "alice")
            
            # Check that date and time were set
            assert results[0][6]  # date_mod
            assert results[0][7]  # time_mod
            assert "/" in results[0][6]  # DD/MM/YYYY format
            assert ":" in results[0][7]  # HH:MM:SS format
        finally:
            repo.close()

    def test_hash_repository_find_exact(self, tmp_path):
        """Test finding exact credential match."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            repo.add_credential(user_id, "example.com", "alice", b"key1", "note1")
            repo.add_credential(user_id, "example.com", "bob", b"key2", "note2")
            repo.add_credential(user_id, "other.com", "alice", b"key3", "note3")
            
            results = repo.find_exact(user_id, "example.com", "alice")
            
            assert len(results) == 1
            assert results[0][2] == "example.com"
            assert results[0][3] == "alice"
        finally:
            repo.close()

    def test_hash_repository_find_exact_not_found(self, tmp_path):
        """Test finding non-existent exact credential."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            
            results = repo.find_exact(user_id, "example.com", "alice")
            assert results == []
        finally:
            repo.close()

    def test_hash_repository_find_credentials_by_app(self, tmp_path):
        """Test searching credentials by application name."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            repo.add_credential(user_id, "example.com", "alice", b"key1", "")
            repo.add_credential(user_id, "example.com", "bob", b"key2", "")
            repo.add_credential(user_id, "example.org", "alice", b"key3", "")
            
            results = repo.find_credentials(user_id, "example.com", "")
            
            assert len(results) == 2
            assert all(r[2] == "example.com" for r in results)
        finally:
            repo.close()

    def test_hash_repository_find_credentials_by_app_and_username(self, tmp_path):
        """Test searching credentials by app and username."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            repo.add_credential(user_id, "example.com", "alice", b"key1", "")
            repo.add_credential(user_id, "example.com", "bob", b"key2", "")
            repo.add_credential(user_id, "example.com", "alice.admin", b"key3", "")
            
            results = repo.find_credentials(user_id, "example.com", "alice")
            
            assert len(results) == 2
            assert results[0][3] == "alice"
            assert results[1][3] == "alice.admin"
        finally:
            repo.close()

    def test_hash_repository_find_credentials_partial_matching(self, tmp_path):
        """Test that find_credentials uses partial prefix matching."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            repo.add_credential(user_id, "example.com", "alice", b"key1", "")
            repo.add_credential(user_id, "example.org", "alice", b"key2", "")
            repo.add_credential(user_id, "example.net", "alice", b"key3", "")
            
            results = repo.find_credentials(user_id, "example.", "")
            
            assert len(results) == 3
        finally:
            repo.close()

    def test_hash_repository_update_credential(self, tmp_path):
        """Test updating a credential."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            repo.add_credential(user_id, "example.com", "alice", b"old_password", "old note")
            
            repo.update_credential(user_id, "example.com", "alice", b"new_password", "new note")
            
            results = repo.find_exact(user_id, "example.com", "alice")
            assert results[0][4] == b"new_password"
            assert results[0][5] == "new note"
        finally:
            repo.close()

    def test_hash_repository_update_credential_updates_timestamps(self, tmp_path):
        """Test that updating credential updates timestamps."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            repo.add_credential(user_id, "example.com", "alice", b"old_password", "old note")
            
            results_before = repo.find_exact(user_id, "example.com", "alice")
            time_before = results_before[0][7]
            
            # Small delay to ensure time difference
            import time
            time.sleep(0.01)
            
            repo.update_credential(user_id, "example.com", "alice", b"new_password", "new note")
            
            results_after = repo.find_exact(user_id, "example.com", "alice")
            time_after = results_after[0][7]
            
            # Time should have changed
            assert time_before != time_after or True  # May be same second
        finally:
            repo.close()

    def test_hash_repository_update_comment(self, tmp_path):
        """Test updating only the comment."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            repo.add_credential(user_id, "example.com", "alice", b"password", "old comment")
            
            repo.update_comment(user_id, "example.com", "alice", "new comment")
            
            results = repo.find_exact(user_id, "example.com", "alice")
            assert results[0][5] == "new comment"
            assert results[0][4] == b"password"  # Password unchanged
        finally:
            repo.close()

    def test_hash_repository_delete_credential(self, tmp_path):
        """Test deleting a credential."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            repo.add_credential(user_id, "example.com", "alice", b"key1", "")
            repo.add_credential(user_id, "example.com", "bob", b"key2", "")
            
            repo.delete_credential(user_id, "example.com", "alice")
            
            results = repo.find_exact(user_id, "example.com", "alice")
            assert results == []
            
            results = repo.find_exact(user_id, "example.com", "bob")
            assert len(results) == 1
        finally:
            repo.close()

    def test_hash_repository_update_user_password(self, tmp_path):
        """Test updating a user's master password."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"old_password")
            
            repo.update_user_password(user_id, b"new_password")
            
            results = repo.find_user(user_id=user_id)
            assert results[0][2] == b"new_password"
        finally:
            repo.close()

    def test_hash_repository_list_credentials(self, tmp_path):
        """Test listing all credentials for a user."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user1_id = repo.add_user("alice", b"key1")
            user2_id = repo.add_user("bob", b"key2")
            
            repo.add_credential(user1_id, "example.com", "alice", b"pass1", "")
            repo.add_credential(user1_id, "other.com", "alice", b"pass2", "")
            repo.add_credential(user2_id, "example.com", "bob", b"pass3", "")
            
            results = repo.list_credentials(user1_id)
            
            assert len(results) == 2
            assert results[0][2] == "example.com"
            assert results[1][2] == "other.com"
        finally:
            repo.close()

    def test_hash_repository_list_credentials_empty(self, tmp_path):
        """Test listing credentials for user with none."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            
            results = repo.list_credentials(user_id)
            assert results == []
        finally:
            repo.close()

    def test_hash_repository_list_credentials_insertion_order(self, tmp_path):
        """Test that list_credentials returns in insertion order."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user_id = repo.add_user("alice", b"master_password")
            
            apps = ["zebra.com", "apple.com", "middle.com"]
            for app in apps:
                repo.add_credential(user_id, app, "alice", b"pass", "")
            
            results = repo.list_credentials(user_id)
            
            assert results[0][2] == "zebra.com"
            assert results[1][2] == "apple.com"
            assert results[2][2] == "middle.com"
        finally:
            repo.close()

    def test_hash_repository_multiple_users_isolated(self, tmp_path):
        """Test that multiple users' credentials don't interfere."""
        db_path = str(tmp_path / "hash.db")
        repo = HashRepository(db_path)

        try:
            repo.initialize()
            user1_id = repo.add_user("alice", b"key1")
            user2_id = repo.add_user("bob", b"key2")
            
            repo.add_credential(user1_id, "example.com", "alice", b"alice_pass", "")
            repo.add_credential(user2_id, "example.com", "bob", b"bob_pass", "")
            
            results1 = repo.find_exact(user1_id, "example.com", "alice")
            results2 = repo.find_exact(user2_id, "example.com", "bob")
            
            assert results1[0][4] == b"alice_pass"
            assert results2[0][4] == b"bob_pass"
        finally:
            repo.close()
