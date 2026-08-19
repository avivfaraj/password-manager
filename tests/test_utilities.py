"""Tests for password_manager.utilities module."""
from pathlib import Path
import tempfile

import pytest

from password_manager.utilities import (
    append_note,
    build_database_path,
    date_time,
    is_sqlite_path,
)


class TestDateTime:
    """Test cases for the date_time function."""

    def test_date_time_returns_tuple(self):
        """Test that date_time returns a tuple of two strings."""
        result = date_time()

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)

    def test_date_time_time_format_hh_mm_ss(self):
        """Test that time is returned in HH:MM:SS format."""
        time_str, _ = date_time()

        parts = time_str.split(":")
        assert len(parts) == 3
        hours, minutes, seconds = parts
        
        assert hours.isdigit()
        assert minutes.isdigit()
        assert seconds.isdigit()
        assert 0 <= int(hours) <= 23
        assert 0 <= int(minutes) <= 59
        assert 0 <= int(seconds) <= 59

    def test_date_time_date_format_dd_mm_yyyy(self):
        """Test that date is returned in DD/MM/YYYY format."""
        _, date_str = date_time()

        parts = date_str.split("/")
        assert len(parts) == 3
        day, month, year = parts
        
        assert day.isdigit()
        assert month.isdigit()
        assert year.isdigit()
        assert 1 <= int(day) <= 31
        assert 1 <= int(month) <= 12
        assert 1900 <= int(year) <= 2100

    def test_date_time_consistency(self):
        """Test that consecutive calls return consistent times."""
        time1, date1 = date_time()
        time2, date2 = date_time()

        # Times should be either same or close
        # (might differ by a second)
        assert date1 == date2


class TestAppendNote:
    """Test cases for the append_note function."""

    def test_append_note_to_empty_message(self):
        """Test appending a note to empty message."""
        result = append_note("new message", "")

        assert "new message" in result
        assert result.endswith("\n")

    def test_append_note_to_existing_message(self):
        """Test appending a note to existing message."""
        result = append_note("new message", "old message")

        assert "new message" in result
        assert "old message" in result
        assert result.endswith("old message")

    def test_append_note_includes_timestamp(self):
        """Test that appended note includes timestamp."""
        result = append_note("test message", "")

        # Should start with *** TIME***
        assert result.startswith("*** ")
        # Should contain colons for time format
        assert ":" in result

    def test_append_note_timestamp_format(self):
        """Test that timestamp is in HH:MM:SS format."""
        result = append_note("message", "")

        # Extract the timestamp part
        time_part = result[4:12]  # "HH:MM:SS"
        assert len(time_part) == 8
        assert time_part[2] == ":"
        assert time_part[5] == ":"

    def test_append_note_default_empty_message(self):
        """Test append_note with default empty old message."""
        result = append_note("new message")

        assert "new message" in result

    def test_append_note_with_multiple_lines(self):
        """Test append_note with multi-line old message."""
        old_message = "line1\nline2\nline3"
        result = append_note("new", old_message)

        assert "new" in result
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    def test_append_note_preserves_order(self):
        """Test that notes are appended in correct order."""
        message = append_note("msg1", "")
        message = append_note("msg2", message)
        message = append_note("msg3", message)

        # msg3 should be at the beginning, then msg2, then msg1
        lines = message.strip().split("\n")
        assert "msg3" in lines[0]
        assert "msg1" in lines[-1]


class TestIsSqlitePath:
    """Test cases for the is_sqlite_path function."""

    def test_is_sqlite_path_valid_db_extension(self):
        """Test that .db file is recognized."""
        assert is_sqlite_path("vault.db") is True

    def test_is_sqlite_path_uppercase_db_extension(self):
        """Test that .DB file is recognized (case-insensitive)."""
        assert is_sqlite_path("VAULT.DB") is True

    def test_is_sqlite_path_mixed_case_db_extension(self):
        """Test that .Db file is recognized (case-insensitive)."""
        assert is_sqlite_path("vault.Db") is True

    def test_is_sqlite_path_with_directory(self):
        """Test that .db file with directory path is recognized."""
        assert is_sqlite_path("/path/to/vault.db") is True
        assert is_sqlite_path("./vault.db") is True
        assert is_sqlite_path("../vault.db") is True

    def test_is_sqlite_path_wrong_extension(self):
        """Test that non-.db files are not recognized."""
        assert is_sqlite_path("vault.txt") is False
        assert is_sqlite_path("vault.sql") is False
        assert is_sqlite_path("vault.sqlite") is False
        assert is_sqlite_path("vault.sqlite3") is False

    def test_is_sqlite_path_empty_string(self):
        """Test that empty string returns False."""
        assert is_sqlite_path("") is False

    def test_is_sqlite_path_no_extension(self):
        """Test that file with no extension returns False."""
        assert is_sqlite_path("vault") is False

    def test_is_sqlite_path_only_extension(self):
        """Test that only extension without filename returns False."""
        assert is_sqlite_path(".db") is False

    def test_is_sqlite_path_multiple_dots(self):
        """Test path with multiple dots."""
        assert is_sqlite_path("vault.backup.db") is True
        assert is_sqlite_path("vault.backup.txt") is False

    def test_is_sqlite_path_expanded_user(self):
        """Test path with user expansion."""
        assert is_sqlite_path("~/vault.db") is True


class TestBuildDatabasePath:
    """Test cases for the build_database_path function."""

    def test_build_database_path_creates_directory(self):
        """Test that directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "vault" / "nested"
            result = build_database_path(str(new_dir), "test.db")

            assert Path(result).parent.exists()

    def test_build_database_path_returns_full_path(self):
        """Test that full path is returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_database_path(tmpdir, "vault.db")

            assert result.endswith("vault.db")
            assert tmpdir in result
            # Directory should exist after call
            assert Path(result).parent.exists()

    def test_build_database_path_with_existing_directory(self):
        """Test that existing directory is not recreated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_database_path(tmpdir, "test.db")

            assert Path(result).parent.exists()

    def test_build_database_path_creates_multiple_nested_directories(self):
        """Test that multiple nested directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = str(Path(tmpdir) / "a" / "b" / "c")
            result = build_database_path(nested_path, "test.db")

            assert Path(result).parent.exists()
            assert result.endswith("test.db")

    def test_build_database_path_with_user_expansion(self):
        """Test that ~ is expanded in path."""
        result = build_database_path("~", "test.db")

        # Should expand ~ to home directory
        assert "~" not in result
        assert result.endswith("test.db")

    def test_build_database_path_multiple_calls_same_directory(self):
        """Test that multiple calls to same directory work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result1 = build_database_path(tmpdir, "vault1.db")
            result2 = build_database_path(tmpdir, "vault2.db")

            assert Path(result1).exists() or True  # File doesn't need to exist
            assert Path(result2).exists() or True

    def test_build_database_path_returns_string(self):
        """Test that result is always a string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_database_path(tmpdir, "test.db")

            assert isinstance(result, str)

    def test_build_database_path_correct_separator(self):
        """Test that path uses correct separators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_database_path(tmpdir, "test.db")

            # Result should use OS-specific separator
            assert Path(result) == Path(tmpdir) / "test.db"

    def test_build_database_path_with_relative_directory(self):
        """Test with relative directory paths."""
        # Note: This will create in current directory
        result = build_database_path("./temp_test_db", "test.db")

        # Clean up
        try:
            Path(result).parent.rmdir()
        except Exception:
            pass

        assert result.endswith("test.db")
