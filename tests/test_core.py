from pathlib import Path

import pytest
import requests

from password_manager.app import PasswordManagerApp, create_services
from password_manager.breach_checker import BreachCheckError, HIBPClient
from password_manager.crypto import EncryptionError, EncryptionService
from password_manager.models import DatabasePair
from password_manager.password_generator import PasswordGenerator, PasswordPolicy
from password_manager.repositories import (
    DatabaseError,
    SQLiteRepository,
    VaultRepositories,
)
from password_manager.services import (
    AuthenticationError,
    AuthenticationService,
    CredentialNotFoundError,
    DuplicateCredentialError,
    VaultService,
)
from password_manager.utilities import append_note, build_database_path, date_time, is_sqlite_path


def test_encryption_service_round_trip_and_failures():
    crypto = EncryptionService()
    key, ciphertext = crypto.encrypt("secret")

    assert crypto.decrypt(key, ciphertext) == "secret"

    with pytest.raises(TypeError, match="plaintext must be a string"):
        crypto.encrypt(123)

    with pytest.raises(EncryptionError, match="Unable to decrypt value"):
        crypto.decrypt(b"not-a-valid-key", b"not-valid-ciphertext")

    other_key = crypto.generate_key()
    with pytest.raises(EncryptionError, match="Unable to decrypt value"):
        crypto.decrypt(other_key, ciphertext)


def test_password_generator_validates_policy_and_strength_messages():
    generator = PasswordGenerator()
    password = generator.generate(PasswordPolicy(letters=8, digits=4, symbols=2))

    assert len(password) == 14
    assert any(character.isupper() for character in password)
    assert any(character.islower() for character in password)
    assert any(character.isdigit() for character in password)

    with pytest.raises(ValueError, match="Password counts cannot be negative"):
        generator.generate(PasswordPolicy(letters=-1, digits=2, symbols=1))

    assert "too short" in generator.strength_message("abc")
    assert "Great!" in generator.strength_message("Abcdef1234!@")  # 12 chars with lowercase, uppercase, digit, symbol
    assert "Good, but could be great" in generator.strength_message("Abcdef1234")  # 10 chars, no symbols
    assert "capital and lowercase" in generator.strength_message("ALLCAPS123")
    assert "numbers" in generator.strength_message("Abcdefghij")
    assert "additional symbols" in generator.strength_message("Abcdef1234")  # 10 chars without symbols from set


def test_hibp_client_returns_match_count_and_raises_on_request_failures():
    class FakeSession:
        def get(self, url, headers=None, timeout=None):
            # SHA1('password') = 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8
            # First 5 chars (prefix) = 5BAA6
            assert url.endswith("5BAA6")
            assert headers["Add-Padding"] == "true"
            assert timeout == 5.0
            return FakeResponse()

    class FakeResponse:
        text = "1E4C9B93F3F0682250B6CF8331B7EE68FD8:7\nOTHER:2\n"  # SHA1('password') suffix

        def raise_for_status(self):
            return None

    client = HIBPClient(timeout=5.0, session=FakeSession())
    assert client.count("password") == 7

    class FailingSession:
        def get(self, *args, **kwargs):
            raise requests.RequestException("network down")

    client = HIBPClient(timeout=1.0, session=FailingSession())
    with pytest.raises(BreachCheckError, match="Unable to reach Have I Been Pwned"):
        client.count("password")


def test_utilities_helpers_and_database_path_builder():
    time_value, date_value = date_time()
    assert len(time_value.split(":")) == 3
    assert len(date_value.split("/")) == 3

    message = append_note("new message", "old message")
    assert message.startswith("*** ")
    assert "new message" in message
    assert message.endswith("old message")

    assert is_sqlite_path("vault.db")
    assert is_sqlite_path("VAULT.DB")
    assert not is_sqlite_path("")
    assert not is_sqlite_path("vault.txt")

    created = build_database_path("/tmp/password_manager_tests", "hash.db")
    assert created.endswith("hash.db")
    # Directory should exist, file doesn't need to exist yet
    assert Path(created).parent.exists()


def test_sqlite_repository_and_vault_repositories_manage_tables_and_errors(tmp_path):
    repo = SQLiteRepository(str(tmp_path / "repo.db"))
    try:
        with pytest.raises(DatabaseError):
            repo.execute("SELECT * FROM missing_table")
    finally:
        repo.close()

    databases = DatabasePair(str(tmp_path / "keys.db"), str(tmp_path / "hash.db"))
    repositories = VaultRepositories(databases)
    try:
        assert repositories.keys.find_user() == []
        assert repositories.hashes.find_user() == []

        user_id = repositories.keys.add_user("alice", b"key")
        assert user_id == 1
        repositories.hashes.add_user("alice", b"hash")

        repositories.keys.add_key(1, "example.com", "alice", b"credential-key")
        rows = repositories.keys.find_key(1, "example.com", "alice")
        assert rows[0][4] == b"credential-key"

        repositories.keys.update_key(1, "example.com", "alice", b"updated-key")
        assert repositories.keys.find_key(1, "example.com", "alice")[0][4] == b"updated-key"

        repositories.hashes.add_credential(1, "example.com", "alice", b"encrypted", "note")
        assert repositories.hashes.find_exact(1, "example.com", "alice")
        repositories.hashes.update_credential(1, "example.com", "alice", b"new-secret", "updated")
        repositories.hashes.update_comment(1, "example.com", "alice", "final note")
        assert repositories.hashes.find_credentials(1, "example", "ali")[0][5] == "final note"

        repositories.keys.delete_key(1, "example.com", "alice")
        repositories.hashes.delete_credential(1, "example.com", "alice")
        assert repositories.hashes.list_credentials(1) == []
    finally:
        repositories.close()


def test_authentication_service_registers_authenticates_and_rejects_invalid_data(tmp_path):
    pair = DatabasePair(str(tmp_path / "keys.db"), str(tmp_path / "hash.db"))
    repositories = VaultRepositories(pair)
    crypto = EncryptionService()
    auth = AuthenticationService(repositories, crypto)

    try:
        with pytest.raises(ValueError, match="Username and password are required"):
            auth.register("", "master")
        with pytest.raises(ValueError, match="Username and password are required"):
            auth.register("alice", "")

        user_id = auth.register("alice", "master")
        assert user_id == 1

        with pytest.raises(AuthenticationError, match="Username already exists"):
            auth.register("alice", "other")

        assert auth.authenticate("alice", "master") == 1

        with pytest.raises(AuthenticationError, match="Username and/or password are incorrect"):
            auth.authenticate("alice", "wrong")
        with pytest.raises(AuthenticationError, match="Username and/or password are incorrect"):
            auth.authenticate("unknown", "master")

        auth.change_master_password(1, "master", "new-password")
        assert auth.authenticate("alice", "new-password") == 1
        assert auth.master_password(1) == "new-password"

        with pytest.raises(AuthenticationError, match="User not found"):
            auth.change_master_password(99, "new-password", "fail")
        with pytest.raises(AuthenticationError, match="Invalid Password"):
            auth.change_master_password(1, "wrong", "new-pass")
    finally:
        repositories.close()


def test_vault_service_handles_add_update_delete_and_not_found_errors(tmp_path):
    pair = DatabasePair(str(tmp_path / "keys.db"), str(tmp_path / "hash.db"))
    repositories = VaultRepositories(pair)
    crypto = EncryptionService()
    auth = AuthenticationService(repositories, crypto)
    vault = VaultService(repositories, crypto)

    try:
        user_id = auth.register("alice", "master")

        with pytest.raises(ValueError, match="Application, username and password are required"):
            vault.add(user_id, "", "alice", "secret", "note")

        vault.add(user_id, "example.com", "alice", "secret", "note")
        with pytest.raises(DuplicateCredentialError, match="That credential already exists"):
            vault.add(user_id, "example.com", "alice", "other", "note")

        stored = vault.get(user_id, "example.com", "alice")
        assert stored.application == "example.com"
        assert stored.username == "alice"
        assert stored.password == "secret"
        assert stored.comment == "note"

        listed = vault.list(user_id)
        assert len(listed) == 1
        assert listed[0].password == "secret"

        matches = vault.search(user_id, "example")
        assert len(matches) == 1
        assert matches[0].username == "alice"

        vault.update(user_id, "example.com", "alice", "new-secret", "updated", True)
        assert vault.get(user_id, "example.com", "alice").password == "new-secret"

        vault.update(user_id, "example.com", "alice", "new-secret", "still here", False)
        assert vault.get(user_id, "example.com", "alice").comment == "still here"

        vault.delete(user_id, "example.com", "alice")
        assert vault.list(user_id) == []

        with pytest.raises(CredentialNotFoundError, match="Credential not found"):
            vault.get(user_id, "example.com", "alice")
        with pytest.raises(CredentialNotFoundError, match="Credential not found"):
            vault.delete(user_id, "missing.com", "alice")
    finally:
        repositories.close()


def test_create_services_validates_database_paths_and_bootstraps_app():
    with pytest.raises(ValueError, match="Both database paths must end in .db"):
        create_services("keys.txt", "hash.db")
    with pytest.raises(ValueError, match="Both database paths must end in .db"):
        create_services("keys.db", "hash.txt")

    repositories, auth_service, vault_service = create_services(
        "keys.db",
        "hash.db",
    )
    try:
        assert repositories.keys is not None
        assert auth_service.repositories is repositories
        assert vault_service.repositories is repositories
    finally:
        repositories.close()

    app = PasswordManagerApp()
    assert app.crypto is not None
    assert app.generator is not None
    assert app.breach_checker is not None
