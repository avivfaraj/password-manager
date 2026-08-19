from dataclasses import dataclass


@dataclass(frozen=True)
class Credential:
    """Represents a credential stored in the vault.

    Attributes
    ----------
    application : str
        Service or application associated with the credential.
    username : str
        Username associated with the credential.
    password : str
        Decrypted password value.
    comment : str
        User-provided note or description.
    time_modified : str
        Time of last modification in ``HH:MM:SS`` format.
    date_modified : str
        Date of last modification in ``DD/MM/YYYY`` format.
    """

    application: str
    username: str
    password: str
    comment: str
    time_modified: str
    date_modified: str


@dataclass(frozen=True)
class DatabasePair:
    """Stores the SQLite paths used by the vault.

    Attributes
    ----------
    keys_path : str
        Path to the key database.
    hash_path : str
        Path to the hash database.
    """

    keys_path: str
    hash_path: str
