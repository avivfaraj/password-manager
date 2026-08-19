import PySimpleGUI as sg

from password_manager.services import AuthenticationError
from password_manager.utilities import is_sqlite_path
from password_manager.gui.manager_view import ManagerView
from password_manager.gui.register_view import RegisterView


class LoginView:
    """Login screen for authenticating an existing user.

    Parameters
    ----------
    crypto : EncryptionService
        Encryption helper used by the application.
    generator : PasswordGenerator
        Password-generation utility for helper dialogs.
    breach_checker : HIBPClient
        API client used to validate password strength.
    pdf_exporter : PDFExporter
        Exporter for generating encrypted PDF backups.
    """

    def __init__(self, crypto, generator, breach_checker, pdf_exporter):
        """Initialize the login view dependencies.

        Parameters
        ----------
        crypto : EncryptionService
            Encryption helper used by the app.
        generator : PasswordGenerator
            Password generation utility.
        breach_checker : HIBPClient
            Breach-checking API client.
        pdf_exporter : PDFExporter
            PDF export utility.
        """
        self.crypto = crypto
        self.generator = generator
        self.breach_checker = breach_checker
        self.pdf_exporter = pdf_exporter

    def run(self):
        """Show the login window and route to registration or the vault manager.

        Returns
        -------
        None
            Displays the login dialog until the user exits or authenticates.
        """
        layout = [
            [sg.Text("Password Manager", font=("Arial", 18))],
            [sg.Text("Hash database"), sg.Input(key="-hash-", size=(45, 1)), sg.FileBrowse()],
            [sg.Text("Key database"), sg.Input(key="-keys-", size=(45, 1)), sg.FileBrowse()],
            [sg.Text("Username"), sg.Input(key="-user-", size=(30, 1))],
            [sg.Text("Password"), sg.Input(key="-pass-", password_char="*", size=(30, 1))],
            [sg.Text("", key="-error-", size=(60, 2), text_color="red")],
            [sg.Button("Register"), sg.Button("Log In"), sg.Button("Exit")],
        ]

        window = sg.Window("Log In", layout, finalize=True)
        try:
            while True:
                event, values = window.read()
                if event in (sg.WIN_CLOSED, "Exit"):
                    return

                if event == "Register":
                    window.hide()
                    try:
                        RegisterView(
                            self.generator, self.breach_checker, self.crypto
                        ).run()
                    finally:
                        window.un_hide()

                elif event == "Log In":
                    keys_path = values["-keys-"]
                    hash_path = values["-hash-"]

                    if not all((keys_path, hash_path, values["-user-"], values["-pass-"])):
                        window["-error-"].update("All fields are required.")
                        continue

                    if not is_sqlite_path(keys_path) or not is_sqlite_path(hash_path):
                        window["-error-"].update("Database files must use the .db extension.")
                        continue

                    try:
                        from password_manager.app import create_services
                        repositories, auth, vault = create_services(keys_path, hash_path)
                        user_id = auth.authenticate(values["-user-"], values["-pass-"])
                    except AuthenticationError as exc:
                        window["-error-"].update(str(exc))
                        continue
                    except Exception as exc:
                        window["-error-"].update(f"Unable to open databases: {exc}")
                        continue

                    window.hide()
                    try:
                        ManagerView(
                            user_id,
                            auth,
                            vault,
                            repositories,
                            self.generator,
                            self.breach_checker,
                            self.pdf_exporter,
                        ).run()
                    finally:
                        repositories.close()
                        window.un_hide()
        finally:
            window.close()
