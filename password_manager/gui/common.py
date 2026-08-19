import PySimpleGUI as sg

from password_manager.breach_checker import BreachCheckError
from password_manager.password_generator import PasswordPolicy
from password_manager.utilities import append_note


THEME = {
    "bg": "#0b1220",
    "panel": "#111827",
    "panel_alt": "#162235",
    "field": "#1d2c42",
    "field_border": "#58708f",
    "text": "#e2e8f0",
    "muted": "#94a3b8",
    "accent": "#5b8def",
    "accent_2": "#f59e0b",
    "success": "#34d399",
    "danger": "#f87171",
    "warning": "#fbbf24",
}


def input_style(key, password=False, size=(30, 1)):
    return sg.Input(
        key=key,
        size=size,
        password_char="*" if password else "",
        background_color=THEME["field"],
        text_color=THEME["text"],
        border_width=1,
        font=("Segoe UI", 11),
        pad=(10, (7, 10)),
        justification="left",
        selected_background_color=THEME["accent"],
        selected_text_color=THEME["text"],
        focus=True,
    )


def multiline_style(key, size, disabled=False):
    return sg.Multiline(
        key=key,
        size=size,
        disabled=disabled,
        background_color=THEME["field"],
        text_color=THEME["text"],
        border_width=1,
        font=("Segoe UI", 10),
        pad=(10, (8, 10)),
    )


def button_style(text, variant="secondary", size=(12, 1), pad=(4, 4)):
    colors = {
        "primary": (THEME["text"], THEME["accent"]),
        "secondary": (THEME["text"], THEME["panel_alt"]),
        "success": (THEME["bg"], THEME["success"]),
        "danger": (THEME["text"], THEME["danger"]),
        "warning": (THEME["bg"], THEME["warning"]),
    }
    return sg.Button(
        text,
        button_color=colors[variant],
        mouseover_colors=(THEME["bg"], THEME["text"]),
        border_width=0,
        use_ttk_buttons=True,
        font=("Segoe UI", 10, "bold"),
        size=size,
        pad=pad,
    )


def browse_style(text, folder=False):
    browse = sg.FolderBrowse if folder else sg.FileBrowse
    return browse(
        text,
        button_color=(THEME["text"], THEME["panel_alt"]),
        font=("Segoe UI", 10, "bold"),
        pad=(6, (7, 10)),
    )


def slider_style(key, default):
    return sg.Slider(
        (0, 20),
        default,
        orientation="h",
        key=key,
        size=(30, 18),
        trough_color=THEME["field_border"],
        background_color=THEME["panel"],
        text_color=THEME["muted"],
        border_width=0,
        pad=(0, (0, 10)),
    )


def field_label(text, color=THEME["muted"]):
    return sg.Text(
        text,
        text_color=color,
        font=("Segoe UI", 10, "bold"),
        pad=((0, 0), (10, 4)),
    )


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
            [sg.Text("Password Generator", font=("Segoe UI", 22, "bold"), text_color=THEME["text"], pad=(0, (20, 10)))],
            [field_label("Digits"), slider_style("-digits-", 4)],
            [field_label("Letters"), slider_style("-letters-", 8)],
            [field_label("Symbols"), slider_style("-symbols-", 4)],
            [field_label("Password"), input_style("-password-", size=(40, 1))],
            [
                button_style("Generate", "primary", (14, 1)),
                button_style("Check Password", "secondary", (16, 1)),
                button_style("Use", "success", (11, 1)),
                button_style("Exit", "danger", (11, 1)),
            ],
            [multiline_style("-message-", (70, 10), disabled=True)],
        ]

        window = sg.Window(
            "Password Helper",
            layout,
            modal=True,
            finalize=True,
            background_color=THEME["bg"],
            element_justification="center",
        )
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
