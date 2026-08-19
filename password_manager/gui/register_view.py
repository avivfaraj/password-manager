import PySimpleGUI as sg

from password_manager.services import AuthenticationError
from password_manager.utilities import build_database_path
from password_manager.gui.common import PasswordHelperView, THEME, browse_style, button_style, input_style


class RegisterView:
    """Registration form for creating a new password manager account.

    Parameters
    ----------
    generator : PasswordGenerator
        Password generator used for password-help dialogs.
    breach_checker : HIBPClient
        Breach checker used for validating generated passwords.
    crypto : EncryptionService
        Crypto service used during registration.
    """

    def __init__(self, generator, breach_checker, crypto):
        """Initialize the registration view dependencies.

        Parameters
        ----------
        generator : PasswordGenerator
            Password-generation utility.
        breach_checker : HIBPClient
            Breach-checking utility.
        crypto : EncryptionService
            Encryption service used for account creation.
        """
        self.generator = generator
        self.breach_checker = breach_checker
        self.crypto = crypto

    def run(self):
        """Display the registration dialog and create the user vault files.

        Returns
        -------
        bool
            ``True`` when registration succeeds, otherwise ``False`` when the user
            exits the dialog.
        """
        layout = [
            [
                sg.Column(
                    [
                        [sg.Text("Create account", font=("Segoe UI", 26, "bold"), text_color=THEME["text"], pad=(0, (20, 10)))],
                        [sg.Text("Set up a secure vault for your passwords.", font=("Segoe UI", 11), text_color=THEME["muted"], pad=(0, (0, 20)))],
                        [sg.Text("", size=(28, 8), background_color=THEME["panel_alt"], pad=(0, (10, 0)))],
                    ],
                    background_color=THEME["panel_alt"],
                    pad=(0, 0),
                    size=(300, 480),
                ),
                sg.Column(
                    [
                        [sg.Text("New vault", font=("Segoe UI", 24, "bold"), text_color=THEME["text"], pad=(0, (25, 10)))],
                        [sg.Text("Hash database directory", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-hash-dir-", size=(38, 1)), browse_style("Browse", folder=True)],
                        [sg.Text("Key database directory", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-keys-dir-", size=(38, 1)), browse_style("Browse", folder=True)],
                        [sg.Text("Username", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-user-", size=(30, 1))],
                        [sg.Text("Password", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-pass-", password=True, size=(30, 1)), button_style("Help", "warning", (8, 1))],
                        [sg.Text("", key="-error-", size=(48, 2), text_color=THEME["danger"], pad=(0, (12, 0)))],
                        [
                            button_style("Register", "success", (12, 1), ((0, 10), 0)),
                            button_style("Exit", "danger", (10, 1)),
                        ],
                    ],
                    background_color=THEME["panel"],
                    pad=(25, 20),
                    size=(520, 480),
                ),
            ]
        ]

        window = sg.Window(
            "Register",
            layout,
            modal=True,
            finalize=True,
            background_color=THEME["bg"],
            size=(830, 520),
        )
        try:
            while True:
                event, values = window.read()

                if event in (sg.WIN_CLOSED, "Exit"):
                    return False

                if event == "Help":
                    generated = PasswordHelperView(
                        self.generator, self.breach_checker
                    ).run()
                    if generated:
                        window["-pass-"].update(generated)

                elif event == "Register":
                    required = (
                        values["-hash-dir-"],
                        values["-keys-dir-"],
                        values["-user-"],
                        values["-pass-"],
                    )
                    if not all(required):
                        window["-error-"].update("All fields are required.")
                        continue

                    hash_path = build_database_path(values["-hash-dir-"], "hash.db")
                    keys_path = build_database_path(values["-keys-dir-"], "keys.db")

                    try:
                        from password_manager.app import create_services
                        repositories, auth, _ = create_services(keys_path, hash_path)
                        try:
                            auth.register(values["-user-"], values["-pass-"])
                        finally:
                            repositories.close()
                    except AuthenticationError as exc:
                        window["-error-"].update(str(exc))
                        continue
                    except Exception as exc:
                        window["-error-"].update(f"Registration failed: {exc}")
                        continue

                    sg.popup_ok("Registration successful.")
                    return True
        finally:
            window.close()
