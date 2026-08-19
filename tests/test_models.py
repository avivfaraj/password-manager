"""Tests for password_manager.models module."""
import pytest

from password_manager.models import Credential, DatabasePair


class TestCredential:
    """Test cases for the Credential data class."""

    def test_credential_initialization_with_valid_data(self):
        """Test creating a Credential with valid data."""
        cred = Credential(
            application="example.com",
            username="alice",
            password="secret123",
            comment="Work account",
            time_modified="14:30:45",
            date_modified="17/08/2026",
        )

        assert cred.application == "example.com"
        assert cred.username == "alice"
        assert cred.password == "secret123"
        assert cred.comment == "Work account"
        assert cred.time_modified == "14:30:45"
        assert cred.date_modified == "17/08/2026"

    def test_credential_is_frozen_immutable(self):
        """Test that Credential instances are immutable (frozen)."""
        cred = Credential(
            application="example.com",
            username="alice",
            password="secret123",
            comment="Work account",
            time_modified="14:30:45",
            date_modified="17/08/2026",
        )

        with pytest.raises(AttributeError):
            cred.password = "newpassword"

    def test_credential_with_empty_comment(self):
        """Test Credential initialization with empty comment."""
        cred = Credential(
            application="example.com",
            username="alice",
            password="secret123",
            comment="",
            time_modified="14:30:45",
            date_modified="17/08/2026",
        )

        assert cred.comment == ""

    def test_credential_equality(self):
        """Test that two Credentials with same values are equal."""
        cred1 = Credential(
            application="example.com",
            username="alice",
            password="secret123",
            comment="Work account",
            time_modified="14:30:45",
            date_modified="17/08/2026",
        )
        cred2 = Credential(
            application="example.com",
            username="alice",
            password="secret123",
            comment="Work account",
            time_modified="14:30:45",
            date_modified="17/08/2026",
        )

        assert cred1 == cred2

    def test_credential_inequality(self):
        """Test that Credentials with different values are not equal."""
        cred1 = Credential(
            application="example.com",
            username="alice",
            password="secret123",
            comment="Work account",
            time_modified="14:30:45",
            date_modified="17/08/2026",
        )
        cred2 = Credential(
            application="different.com",
            username="alice",
            password="secret123",
            comment="Work account",
            time_modified="14:30:45",
            date_modified="17/08/2026",
        )

        assert cred1 != cred2


class TestDatabasePair:
    """Test cases for the DatabasePair data class."""

    def test_database_pair_initialization(self):
        """Test creating a DatabasePair with valid paths."""
        pair = DatabasePair(keys_path="/tmp/keys.db", hash_path="/tmp/hash.db")

        assert pair.keys_path == "/tmp/keys.db"
        assert pair.hash_path == "/tmp/hash.db"

    def test_database_pair_is_frozen_immutable(self):
        """Test that DatabasePair instances are immutable."""
        pair = DatabasePair(keys_path="/tmp/keys.db", hash_path="/tmp/hash.db")

        with pytest.raises(AttributeError):
            pair.keys_path = "/tmp/other.db"

    def test_database_pair_equality(self):
        """Test that two DatabasePairs with same paths are equal."""
        pair1 = DatabasePair(keys_path="/tmp/keys.db", hash_path="/tmp/hash.db")
        pair2 = DatabasePair(keys_path="/tmp/keys.db", hash_path="/tmp/hash.db")

        assert pair1 == pair2

    def test_database_pair_inequality(self):
        """Test that DatabasePairs with different paths are not equal."""
        pair1 = DatabasePair(keys_path="/tmp/keys.db", hash_path="/tmp/hash.db")
        pair2 = DatabasePair(keys_path="/tmp/keys.db", hash_path="/tmp/other.db")

        assert pair1 != pair2

    def test_database_pair_with_relative_paths(self):
        """Test DatabasePair with relative paths."""
        pair = DatabasePair(keys_path="./keys.db", hash_path="./hash.db")

        assert pair.keys_path == "./keys.db"
        assert pair.hash_path == "./hash.db"

    def test_database_pair_with_expanduser_paths(self):
        """Test DatabasePair with user-expanded paths."""
        pair = DatabasePair(keys_path="~/vault/keys.db", hash_path="~/vault/hash.db")

        assert "~" in pair.keys_path
        assert "~" in pair.hash_path
