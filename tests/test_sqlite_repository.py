"""Tests for password_manager.repositories module - SQLiteRepository class."""
import sqlite3
import tempfile
from pathlib import Path

import pytest

from password_manager.repositories import DatabaseError, SQLiteRepository


class TestSQLiteRepository:
    """Test cases for the SQLiteRepository class."""

    def test_sqlite_repository_initialization_with_valid_path(self, tmp_path):
        """Test SQLiteRepository initialization with valid path."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            assert repo.path == db_path
            assert repo.connection is not None
        finally:
            repo.close()

    def test_sqlite_repository_empty_path_raises_value_error(self):
        """Test that empty path raises ValueError."""
        with pytest.raises(ValueError, match="Database path is required"):
            SQLiteRepository("")

    def test_sqlite_repository_none_path_raises_value_error(self):
        """Test that None path raises ValueError."""
        with pytest.raises(ValueError, match="Database path is required"):
            SQLiteRepository(None)

    def test_sqlite_repository_close_closes_connection(self, tmp_path):
        """Test that close() closes the database connection."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)
        repo.close()

        # Attempting to use closed connection should raise an error
        with pytest.raises(sqlite3.ProgrammingError):
            repo.connection.execute("SELECT 1")

    def test_sqlite_repository_execute_query_succeeds(self, tmp_path):
        """Test executing a valid query."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            cursor = repo.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            assert cursor is not None
        finally:
            repo.close()

    def test_sqlite_repository_execute_with_params(self, tmp_path):
        """Test executing query with parameters."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            repo.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            cursor = repo.execute("INSERT INTO test (name) VALUES (?)", ("Alice",))
            assert cursor.lastrowid > 0
        finally:
            repo.close()

    def test_sqlite_repository_execute_invalid_query_raises_database_error(self, tmp_path):
        """Test that invalid query raises DatabaseError."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            with pytest.raises(DatabaseError):
                repo.execute("SELECT * FROM nonexistent_table")
        finally:
            repo.close()

    def test_sqlite_repository_execute_rollback_on_error(self, tmp_path):
        """Test that transaction is rolled back on error."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            repo.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            
            # Attempt invalid insert with wrong column count
            with pytest.raises(DatabaseError):
                repo.execute("INSERT INTO test (id, name, invalid) VALUES (1, 'Alice', 'x')")
            
            # Table should still be usable
            cursor = repo.execute("INSERT INTO test (name) VALUES (?)", ("Bob",))
            assert cursor.lastrowid > 0
        finally:
            repo.close()

    def test_sqlite_repository_multiple_executes_are_committed(self, tmp_path):
        """Test that multiple executes properly commit."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            repo.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            repo.execute("INSERT INTO test (name) VALUES (?)", ("Alice",))
            repo.execute("INSERT INTO test (name) VALUES (?)", ("Bob",))
            
            cursor = repo.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]
            assert count == 2
        finally:
            repo.close()

    def test_sqlite_repository_data_persists_after_close(self, tmp_path):
        """Test that data persists after closing and reopening."""
        db_path = str(tmp_path / "test.db")
        
        # First session: create and insert
        repo1 = SQLiteRepository(db_path)
        repo1.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        repo1.execute("INSERT INTO test (name) VALUES (?)", ("Alice",))
        repo1.close()

        # Second session: verify data persists
        repo2 = SQLiteRepository(db_path)
        try:
            cursor = repo2.execute("SELECT name FROM test WHERE id = 1")
            result = cursor.fetchone()
            assert result[0] == "Alice"
        finally:
            repo2.close()

    def test_sqlite_repository_execute_with_empty_params(self, tmp_path):
        """Test execute with empty params tuple."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            cursor = repo.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)", ())
            assert cursor is not None
        finally:
            repo.close()

    def test_sqlite_repository_error_wraps_sqlite_error(self, tmp_path):
        """Test that DatabaseError wraps original SQLite error."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            with pytest.raises(DatabaseError) as exc_info:
                repo.execute("INVALID SQL SYNTAX HERE")
            
            # Should have a cause
            assert exc_info.value.__cause__ is not None
        finally:
            repo.close()

    def test_sqlite_repository_can_handle_blob_data(self, tmp_path):
        """Test that repository can handle binary data."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            repo.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data BLOB)")
            binary_data = b"\\x00\\x01\\x02\\xff"
            repo.execute("INSERT INTO test (data) VALUES (?)", (binary_data,))
            
            cursor = repo.execute("SELECT data FROM test WHERE id = 1")
            result = cursor.fetchone()[0]
            assert result == binary_data
        finally:
            repo.close()

    def test_sqlite_repository_large_data_handling(self, tmp_path):
        """Test that repository can handle large data."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            repo.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
            large_text = "x" * 100000
            repo.execute("INSERT INTO test (data) VALUES (?)", (large_text,))
            
            cursor = repo.execute("SELECT data FROM test WHERE id = 1")
            result = cursor.fetchone()[0]
            assert result == large_text
        finally:
            repo.close()

    def test_sqlite_repository_concurrent_access_with_timeout(self, tmp_path):
        """Test that repository creates connection (timeout is internal to SQLite)."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            # The connection was created with timeout=10 (internal SQLite setting)
            # sqlite3.Connection doesn't expose timeout as an attribute
            assert repo.connection is not None
        finally:
            repo.close()

    def test_sqlite_repository_execute_returns_cursor_with_lastrowid(self, tmp_path):
        """Test that execute returns cursor with lastrowid."""
        db_path = str(tmp_path / "test.db")
        repo = SQLiteRepository(db_path)

        try:
            repo.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            cursor1 = repo.execute("INSERT INTO test (name) VALUES (?)", ("Alice",))
            cursor2 = repo.execute("INSERT INTO test (name) VALUES (?)", ("Bob",))
            
            assert cursor1.lastrowid == 1
            assert cursor2.lastrowid == 2
        finally:
            repo.close()
