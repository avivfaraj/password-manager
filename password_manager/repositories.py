import sqlite3

from password_manager.models import DatabasePair
from password_manager.utilities import date_time


class DatabaseError(Exception):
    """Exception raised when a repository operation fails.

    This wraps SQLite errors that occur while executing queries or committing
    database changes.
    """


class SQLiteRepository:
    """Base wrapper for SQLite database access.

    Parameters
    ----------
    path : str
        Path to the SQLite database file.

    Raises
    ------
    ValueError
        If the database path is empty.
    """

    def __init__(self, path: str):
        """Open a SQLite connection for the provided database file.

        Parameters
        ----------
        path : str
            Database file path.

        Raises
        ------
        ValueError
            If ``path`` is empty.
        """
        if not path:
            raise ValueError("Database path is required")
        self.path = path
        self.connection = sqlite3.connect(path, timeout=10)

    def close(self):
        """Close the database connection.

        Returns
        -------
        None
        """
        self.connection.close()

    def execute(self, query: str, params: tuple = ()):
        """Execute a SQL query and commit the transaction.

        Parameters
        ----------
        query : str
            SQL statement to execute.
        params : tuple, optional
            Query parameters. The default is ().

        Returns
        -------
        sqlite3.Cursor
            Cursor returned by the database call.

        Raises
        ------
        DatabaseError
            If the SQL statement fails and the transaction is rolled back.
        """
        try:
            cursor = self.connection.execute(query, params)
            self.connection.commit()
            return cursor
        except sqlite3.Error as exc:
            self.connection.rollback()
            raise DatabaseError(str(exc)) from exc


class KeysRepository(SQLiteRepository):
    """Repository for storing user key material used in the vault.

    This repository is responsible for saving master-password keys and per-entry
    encryption keys used to decrypt credential data.
    """

    def initialize(self):
        """Create the keys tables if they do not already exist.

        Returns
        -------
        None
        """
        self.execute(
            "CREATE TABLE IF NOT EXISTS users "
            "(id INTEGER PRIMARY KEY, username TEXT, hash BLOB)"
        )
        self.execute(
            "CREATE TABLE IF NOT EXISTS list "
            "(id INTEGER PRIMARY KEY, user_id INTEGER, app TEXT, username TEXT, key BLOB)"
        )

    def add_user(self, username, encrypted_password):
        """Insert a new user row and return its primary key.

        Parameters
        ----------
        username : str
            User name to store.
        encrypted_password : bytes
            Encrypted master password for the user.

        Returns
        -------
        int
            Primary key assigned to the new user.
        """
        return self.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            (username, encrypted_password),
        ).lastrowid

    def find_user(self, username=None, user_id=None):
        """Look up a user by username or user id.

        Parameters
        ----------
        username : str, optional
            User name to search for.
        user_id : int, optional
            User id to search for.

        Returns
        -------
        list
            Matching user records.
        """
        if username is not None:
            return self.connection.execute(
                "SELECT id, username, hash FROM users WHERE username = ?", (username,)
            ).fetchall()
        if user_id is not None:
            return self.connection.execute(
                "SELECT id, username, hash FROM users WHERE id = ?", (user_id,)
            ).fetchall()
        return []

    def add_key(self, user_id, application, username, key):
        """Store an encryption key for a specific credential entry.

        Parameters
        ----------
        user_id : int
            User who owns the credential.
        application : str
            Application name associated with the credential.
        username : str
            Username associated with the credential.
        key : bytes
            Encryption key for that credential.
        """
        self.execute(
            "INSERT INTO list (user_id, app, username, key) VALUES (?, ?, ?, ?)",
            (user_id, application, username, key),
        )

    def find_key(self, user_id, application, username):
        """Fetch the key record for an application and username.

        Parameters
        ----------
        user_id : int
            User owner id.
        application : str
            Application name to match.
        username : str
            Username to match.

        Returns
        -------
        list
            Matching key records.
        """
        return self.connection.execute(
            "SELECT id, user_id, app, username, key FROM list "
            "WHERE user_id = ? AND app = ? AND username = ?",
            (user_id, application, username),
        ).fetchall()

    def update_key(self, user_id, application, username, key):
        """Replace the encryption key for an existing credential.

        Parameters
        ----------
        user_id : int
            User owner id.
        application : str
            Application name to update.
        username : str
            Username to update.
        key : bytes
            New encryption key to store.
        """
        self.execute(
            "UPDATE list SET key = ? WHERE user_id = ? AND app = ? AND username = ?",
            (key, user_id, application, username),
        )

    def delete_key(self, user_id, application, username):
        """Delete the key record for a credential.

        Parameters
        ----------
        user_id : int
            User owner id.
        application : str
            Application name to remove.
        username : str
            Username to remove.
        """
        self.execute(
            "DELETE FROM list WHERE user_id = ? AND app = ? AND username = ?",
            (user_id, application, username),
        )

    def update_user_password(self, user_id, key):
        """Update the encrypted master password for a user.

        Parameters
        ----------
        user_id : int
            User id to update.
        key : bytes
            Newly encrypted master password.
        """
        self.execute("UPDATE users SET hash = ? WHERE id = ?", (key, user_id))

    def list_keys(self, user_id):
        """Return all key records for a user.

        Parameters
        ----------
        user_id : int
            User id whose keys should be listed.

        Returns
        -------
        list
            Key rows in insertion order.
        """
        return self.connection.execute(
            "SELECT id, user_id, app, username, key FROM list "
            "WHERE user_id = ? ORDER BY id ASC", (user_id,)
        ).fetchall()


class HashRepository(SQLiteRepository):
    """Repository for encrypted credential metadata and password values.

    This repository stores the encrypted password payload and record details such
    as comments and modification timestamps.
    """

    def initialize(self):
        """Create the credential tables if they do not already exist.

        Returns
        -------
        None
        """
        self.execute(
            "CREATE TABLE IF NOT EXISTS users "
            "(id INTEGER PRIMARY KEY, username TEXT, hash BLOB)"
        )
        self.execute(
            "CREATE TABLE IF NOT EXISTS list "
            "(id INTEGER PRIMARY KEY, user_id INTEGER, app TEXT, username TEXT, "
            "hash BLOB, comment TEXT, date_mod TEXT, time_mod TEXT)"
        )

    def add_user(self, username, encrypted_password):
        """Insert a new user into the hash database.

        Parameters
        ----------
        username : str
            User name to store.
        encrypted_password : bytes
            Encrypted master password associated with the user.

        Returns
        -------
        int
            Primary key assigned to the new user.
        """
        return self.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            (username, encrypted_password),
        ).lastrowid

    def find_user(self, username=None, user_id=None):
        """Look up a user row by username or id.

        Parameters
        ----------
        username : str, optional
            Username to search for.
        user_id : int, optional
            User id to search for.

        Returns
        -------
        list
            Matching user rows.
        """
        if username is not None:
            return self.connection.execute(
                "SELECT id, username, hash FROM users WHERE username = ?", (username,)
            ).fetchall()
        if user_id is not None:
            return self.connection.execute(
                "SELECT id, username, hash FROM users WHERE id = ?", (user_id,)
            ).fetchall()
        return []

    def add_credential(self, user_id, application, username, ciphertext, comment):
        """Insert an encrypted credential record into the repo.

        Parameters
        ----------
        user_id : int
            User owner id.
        application : str
            Application name.
        username : str
            Username for the account.
        ciphertext : bytes
            Encrypted credential password.
        comment : str
            User comment text.
        """
        time, date = date_time()
        self.execute(
            "INSERT INTO list "
            "(user_id, app, username, hash, comment, date_mod, time_mod) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, application, username, ciphertext, comment, date, time),
        )

    def find_exact(self, user_id, application, username):
        """Find a credential matching the exact app and username.

        Parameters
        ----------
        user_id : int
            User owner id.
        application : str
            Application name.
        username : str
            Username.

        Returns
        -------
        list
            Matching credential rows.
        """
        return self.connection.execute(
            "SELECT * FROM list WHERE user_id = ? AND app = ? AND username = ?",
            (user_id, application, username),
        ).fetchall()

    def find_credentials(self, user_id, application="", username=""):
        """Search for credentials using partial app or username filters.

        Parameters
        ----------
        user_id : int
            User owner id.
        application : str, optional
            Prefix to match against application names.
        username : str, optional
            Prefix to match against usernames.

        Returns
        -------
        list
            Matching credential rows.
        """
        if username:
            return self.connection.execute(
                "SELECT * FROM list WHERE user_id = ? AND app LIKE ? AND username LIKE ?",
                (user_id, application + "%", username + "%"),
            ).fetchall()
        return self.connection.execute(
            "SELECT * FROM list WHERE user_id = ? AND app LIKE ?",
            (user_id, application + "%"),
        ).fetchall()

    def update_credential(self, user_id, application, username, ciphertext, comment):
        """Replace a credential's encrypted password and metadata.

        Parameters
        ----------
        user_id : int
            User owner id.
        application : str
            Application name.
        username : str
            Username for the credential.
        ciphertext : bytes
            New encrypted password value.
        comment : str
            Updated note text.
        """
        time, date = date_time()
        self.execute(
            "UPDATE list SET hash = ?, comment = ?, time_mod = ?, date_mod = ? "
            "WHERE user_id = ? AND app = ? AND username = ?",
            (ciphertext, comment, time, date, user_id, application, username),
        )

    def update_comment(self, user_id, application, username, comment):
        """Update only the comment field for a credential.

        Parameters
        ----------
        user_id : int
            User owner id.
        application : str
            Application name.
        username : str
            Username to update.
        comment : str
            New comment text.
        """
        self.execute(
            "UPDATE list SET comment = ? WHERE user_id = ? AND app = ? AND username = ?",
            (comment, user_id, application, username),
        )

    def delete_credential(self, user_id, application, username):
        """Delete a credential record from the vault.

        Parameters
        ----------
        user_id : int
            User owner id.
        application : str
            Application name.
        username : str
            Username for the credential.
        """
        self.execute(
            "DELETE FROM list WHERE user_id = ? AND app = ? AND username = ?",
            (user_id, application, username),
        )

    def update_user_password(self, user_id, ciphertext):
        """Update the encrypted master password for a user.

        Parameters
        ----------
        user_id : int
            User id to update.
        ciphertext : bytes
            Newly encrypted master password.
        """
        self.execute("UPDATE users SET hash = ? WHERE id = ?", (ciphertext, user_id))

    def list_credentials(self, user_id):
        """Return all credential rows for a user.

        Parameters
        ----------
        user_id : int
            User id whose credentials are being listed.

        Returns
        -------
        list
            All credential rows in insertion order.
        """
        return self.connection.execute(
            "SELECT * FROM list WHERE user_id = ? ORDER BY id ASC", (user_id,)
        ).fetchall()


class VaultRepositories:
    """Container for the key and credential repositories.

    Parameters
    ----------
    databases : DatabasePair
        Pair of database paths used by the vault.
    """

    def __init__(self, databases: DatabasePair):
        """Initialize both repositories and create their schemas.

        Parameters
        ----------
        databases : DatabasePair
            Database paths for the key and hash stores.
        """
        self.keys = KeysRepository(databases.keys_path)
        self.hashes = HashRepository(databases.hash_path)
        self.keys.initialize()
        self.hashes.initialize()

    def close(self):
        """Close both repository connections.

        Returns
        -------
        None
        """
        self.keys.close()
        self.hashes.close()
