import PySimpleGUI as sg

from password_manager.services import AuthenticationError
from password_manager.utilities import build_database_path
from password_manager.gui.common import PasswordHelperView


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
            [sg.Text("Create Password Manager", font=("Arial", 16))],
            [sg.Text("Hash database directory"), sg.Input(key="-hash-dir-"), sg.FolderBrowse()],
            [sg.Text("Key database directory"), sg.Input(key="-keys-dir-"), sg.FolderBrowse()],
            [sg.Text("Username"), sg.Input(key="-user-")],
            [sg.Text("Password"), sg.Input(key="-pass-", password_char="*"), sg.Button("Help")],
            [sg.Text("", key="-error-", size=(60, 2), text_color="red")],
            [sg.Button("Register"), sg.Button("Exit")],
        ]

        window = sg.Window("Register", layout, modal=True, finalize=True)
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
