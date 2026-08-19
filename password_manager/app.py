import PySimpleGUI as sg

from password_manager.breach_checker import HIBPClient
from password_manager.crypto import EncryptionService
from password_manager.models import DatabasePair
from password_manager.password_generator import PasswordGenerator
from password_manager.pdf_exporter import PDFExporter
from password_manager.repositories import VaultRepositories
from password_manager.services import AuthenticationService, VaultService
from password_manager.utilities import is_sqlite_path
from password_manager.gui.login_view import LoginView


def create_services(keys_path, hash_path):
    """Create the repository and service layer for the password manager.

    Parameters
    ----------
    keys_path : str
        File system path to the SQLite database that stores encryption keys.
    hash_path : str
        File system path to the SQLite database that stores encrypted credentials.

    Returns
    -------
    tuple
        A tuple containing the repositories, authentication service, and vault service.

    Raises
    ------
    ValueError
        If either database path does not end with the ``.db`` extension.
    """
    if not is_sqlite_path(keys_path) or not is_sqlite_path(hash_path):
        raise ValueError("Both database paths must end in .db")

    repositories = VaultRepositories(DatabasePair(keys_path, hash_path))
    crypto = EncryptionService()
    return (
        repositories,
        AuthenticationService(repositories, crypto),
        VaultService(repositories, crypto),
    )


class PasswordManagerApp:
    """Top-level application wrapper for the password manager GUI.

    Attributes
    ----------
    crypto : EncryptionService
        Encryption helper for user and credential secrets.
    generator : PasswordGenerator
        Password generation and password-strength utility.
    breach_checker : HIBPClient
        Client used to check whether a password appears in known breaches.
    pdf_exporter : PDFExporter
        Exporter used to create encrypted PDF backups.
    """

    def __init__(self):
        """Initialize the services used by the application."""
        self.crypto = EncryptionService()
        self.generator = PasswordGenerator()
        self.breach_checker = HIBPClient()
        self.pdf_exporter = PDFExporter()

    def run(self):
        """Launch the login view and begin the application lifecycle."""
        sg.theme("DarkTeal12")
        LoginView(
            self.crypto,
            self.generator,
            self.breach_checker,
            self.pdf_exporter,
        ).run()


if __name__ == "__main__":
    PasswordManagerApp().run()
