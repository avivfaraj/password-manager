import PySimpleGUI as sg

from password_manager.services import AuthenticationError
from password_manager.utilities import is_sqlite_path
from password_manager.gui.common import THEME, browse_style, button_style, input_style
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
            [
                sg.Column(
                    [
                        [sg.Text("VaultGuard", font=("Segoe UI", 30, "bold"), text_color=THEME["text"], pad=(0, (10, 6)))],
                        [sg.Text("Secure password management", font=("Segoe UI", 12), text_color=THEME["muted"], pad=(0, (0, 20)))],
                        [sg.Text("Your vault is protected by end-to-end encryption and secure key storage.", font=("Segoe UI", 11), text_color=THEME["muted"], pad=(0, (0, 10)))],
                        [sg.Text("", size=(26, 8), background_color=THEME["panel_alt"], pad=(0, (20, 0)))],
                    ],
                    background_color=THEME["panel_alt"],
                    pad=(0, 0),
                    size=(340, 520),
                ),
                sg.Column(
                    [
                        [sg.Text("Welcome back", font=("Segoe UI", 24, "bold"), text_color=THEME["text"], pad=(0, (30, 10)))],
                        [sg.Text("Hash database", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-hash-", size=(42, 1)), browse_style("Browse")],
                        [sg.Text("Key database", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-keys-", size=(42, 1)), browse_style("Browse")],
                        [sg.Text("Username", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-user-", size=(30, 1))],
                        [sg.Text("Password", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-pass-", password=True, size=(30, 1))],
                        [sg.Text("", key="-error-", size=(48, 2), text_color=THEME["danger"], pad=(0, (10, 0)))],
                        [
                            button_style("Register", "secondary", (12, 1), ((0, 10), 0)),
                            button_style("Log In", "primary", (12, 1), ((0, 10), 0)),
                            button_style("Exit", "danger", (10, 1)),
                        ],
                    ],
                    background_color=THEME["panel"],
                    pad=(25, 20),
                    size=(520, 520),
                ),
            ]
        ]

        window = sg.Window(
            "Log In",
            layout,
            finalize=True,
            background_color=THEME["bg"],
            size=(900, 560),
            resizable=True,
        )
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
