import PySimpleGUI as sg

from password_manager.breach_checker import BreachCheckError
from password_manager.password_generator import PasswordPolicy
from password_manager.utilities import append_note


class PasswordHelperView:
    """Dialog for generating and validating passwords.

    Parameters
    ----------
    generator : PasswordGenerator
        Object used to create randomized passwords.
    breach_checker : HIBPClient
        Client used to check whether a password has appeared in known breaches.
    """

    def __init__(self, generator, breach_checker):
        """Initialize the helper with a generator and breach checker.

        Parameters
        ----------
        generator : PasswordGenerator
            Password-generation utility.
        breach_checker : HIBPClient
            Breach-checking utility.
        """
        self.generator = generator
        self.breach_checker = breach_checker

    def run(self):
        """Display the password helper and return the selected password.

        Returns
        -------
        str
            The password chosen by the user or an empty string if the dialog is
            closed without selection.
        """
        layout = [
            [sg.Text("Password Generator", font=("Arial", 16))],
            [sg.Text("Digits"), sg.Slider((0, 20), 4, orientation="h", key="-digits-")],
            [sg.Text("Letters"), sg.Slider((0, 20), 8, orientation="h", key="-letters-")],
            [sg.Text("Symbols"), sg.Slider((0, 20), 4, orientation="h", key="-symbols-")],
            [sg.Text("Password"), sg.Input(key="-password-", size=(40, 1))],
            [sg.Button("Generate"), sg.Button("Check Password"), sg.Button("Use"), sg.Button("Exit")],
            [sg.Multiline(size=(70, 10), key="-message-", disabled=True)],
        ]

        window = sg.Window("Password Helper", layout, modal=True, finalize=True)
        try:
            while True:
                event, values = window.read()
                if event in (sg.WIN_CLOSED, "Exit"):
                    return ""

                if event == "Generate":
                    policy = PasswordPolicy(
                        letters=int(values["-letters-"]),
                        digits=int(values["-digits-"]),
                        symbols=int(values["-symbols-"]),
                    )
                    password = self.generator.generate(policy)
                    window["-password-"].update(password)
                    msg = "Password generated."
                    if len(password) < 8:
                        msg += " More than 8 characters is recommended."
                    window["-message-"].update(append_note(msg, values["-message-"]))

                elif event == "Check Password":
                    password = values["-password-"]
                    if not password:
                        msg = "Please enter password!"
                    else:
                        try:
                            count = self.breach_checker.count(password)
                            msg = (
                                f"Password was leaked! It appears {count} times in the database."
                                if count
                                else self.generator.strength_message(password)
                            )
                        except BreachCheckError:
                            msg = "Error: No internet connection or HIBP is unavailable."
                    window["-message-"].update(append_note(msg, values["-message-"]))

                elif event == "Use":
                    return values["-password-"]
        finally:
            window.close()
