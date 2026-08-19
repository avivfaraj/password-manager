from datetime import datetime
from pathlib import Path


def date_time() -> tuple[str, str]:
    """Return the current time and date in a display-friendly format.

    Returns
    -------
    tuple[str, str]
        A pair containing the current time as ``HH:MM:SS`` and the current date as
        ``DD/MM/YYYY``.
    """
    now = datetime.now()
    return now.strftime("%H:%M:%S"), now.strftime("%d/%m/%Y")


def append_note(new_message: str, old_message: str = "") -> str:
    """Append a timestamped note to an existing message string.

    Parameters
    ----------
    new_message : str
        Message to append with a timestamp.
    old_message : str, optional
        Existing text to preserve before the new entry. The default is ``""``.

    Returns
    -------
    str
        Combined message block with the new entry prefixed by a timestamp.
    """
    time, _ = date_time()
    return f"*** {time}*** {new_message}\n{old_message}"


def is_sqlite_path(path: str) -> bool:
    """Check whether the supplied path points to an SQLite database file.

    Parameters
    ----------
    path : str
        Candidate file path to inspect.

    Returns
    -------
    bool
        ``True`` if the path is non-empty and ends with the ``.db`` suffix.
    """
    return bool(path) and Path(path).suffix.lower() == ".db"


def build_database_path(directory: str, filename: str) -> str:
    """Create a directory if needed and return a fully qualified database path.

    Parameters
    ----------
    directory : str
        Directory to create or use.
    filename : str
        Database file name, such as ``hash.db``.

    Returns
    -------
    str
        Full path to the database file.
    """
    directory_path = Path(directory).expanduser()
    directory_path.mkdir(parents=True, exist_ok=True)
    return str(directory_path / filename)
