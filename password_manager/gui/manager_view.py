import PySimpleGUI as sg

from password_manager.services import CredentialNotFoundError, DuplicateCredentialError
from password_manager.utilities import append_note
from password_manager.gui.common import PasswordHelperView, THEME, button_style, input_style, multiline_style


class ManagerView:
    """Main GUI for managing a user's stored credentials.

    Parameters
    ----------
    user_id : int
        Identifier for the authenticated user.
    auth : AuthenticationService
        Authentication service responsible for managing the user account.
    vault : VaultService
        Service for creating, reading, updating, and deleting credentials.
    repositories : VaultRepositories
        Repository bundle for persistence.
    generator : PasswordGenerator
        Password-generation utility used in helper dialogs.
    breach_checker : HIBPClient
        Password-breach validation client.
    pdf_exporter : PDFExporter
        PDF export utility.
    """

    def __init__(
        self,
        user_id,
        auth,
        vault,
        repositories,
        generator,
        breach_checker,
        pdf_exporter,
    ):
        """Initialize the manager view and set the selected credential state.

        Parameters
        ----------
        user_id : int
            Active user identifier.
        auth : AuthenticationService
            Authentication logic for the user.
        vault : VaultService
            Credential management service.
        repositories : VaultRepositories
            Repository objects that persist the user's vault.
        generator : PasswordGenerator
            Helper object for generating passwords.
        breach_checker : HIBPClient
            API client for checking password breaches.
        pdf_exporter : PDFExporter
            Export service used for PDF backups.
        """
        self.user_id = user_id
        self.auth = auth
        self.vault = vault
        self.repositories = repositories
        self.generator = generator
        self.breach_checker = breach_checker
        self.pdf_exporter = pdf_exporter
        self.selected = None
        self.credentials = []

    def _layout(self):
        """Create the main layout of the manager window.

        Returns
        -------
            list
            PySimpleGUI layout definition for the manager form and credential table.
        """
        return [
            [
                sg.Text("Vault Dashboard", font=("Segoe UI", 28, "bold"), text_color=THEME["text"], pad=(20, (20, 10))),
                sg.Push(),
                sg.Text("Secure workspace", font=("Segoe UI", 11), text_color=THEME["muted"], pad=(0, (26, 0))),
            ],
            [
                sg.Column(
                    [
                        [sg.Text("Credentials", font=("Segoe UI", 16, "bold"), text_color=THEME["text"], pad=(0, (0, 10)))],
                        [sg.Table(
                            values=[],
                            headings=["Application", "Username", "Last changed", "Date"],
                            key="-list-",
                            enable_events=True,
                            select_mode="browse",
                            justification="left",
                            col_widths=[16, 15, 12, 10],
                            auto_size_columns=False,
                            row_height=28,
                            font=("Segoe UI", 10),
                            header_font=("Segoe UI", 10, "bold"),
                            header_text_color=THEME["text"],
                            header_background_color=THEME["panel_alt"],
                            header_border_width=0,
                            text_color=THEME["text"],
                            background_color=THEME["field"],
                            alternating_row_color=THEME["panel_alt"],
                            selected_row_colors=(THEME["text"], THEME["accent"]),
                            border_width=0,
                            size=(50, 12),
                            pad=(0, (0, 10)),
                        )],
                        [button_style("Search", "secondary", (12, 1), (0, (10, 0)))],
                    ],
                    background_color=THEME["panel"],
                    pad=(20, 0),
                ),
                sg.Column(
                    [
                        [sg.Text("Credential details", font=("Segoe UI", 16, "bold"), text_color=THEME["text"], pad=(0, (0, 10)))],
                        [sg.Text("Application", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-app-", size=(32, 1))],
                        [sg.Text("Username", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-user-", size=(32, 1))],
                        [sg.Text("Password", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [input_style("-pass-", size=(32, 1)), button_style("Help", "warning", (8, 1))],
                        [sg.Text("Comment", text_color=THEME["muted"], font=("Segoe UI", 10, "bold"), pad=(0, (10, 3)))],
                        [multiline_style("-comment-", (34, 5))],
                        [
                            button_style("Add", "success", (11, 1), ((0, 10), 0)),
                            button_style("Update", "primary", (11, 1), ((0, 10), 0)),
                            button_style("Delete", "danger", (11, 1)),
                        ],
                    ],
                    background_color=THEME["panel"],
                    pad=(10, 0),
                ),
            ],
            [
                sg.Column(
                    [
                        [sg.Text("Activity log", font=("Segoe UI", 16, "bold"), text_color=THEME["text"], pad=(0, (0, 6)))],
                        [multiline_style("-message-", (108, 6), disabled=True)],
                    ],
                    background_color=THEME["panel"],
                    pad=(20, (10, 0)),
                ),
            ],
            [
                button_style("Change Master Password", "secondary", (20, 1), (20, (10, 10))),
                button_style("Create PDF", "primary", (15, 1), (0, (10, 10))),
                button_style("Exit", "danger", (12, 1), (0, (10, 10))),
            ],
        ]

    def _message(self, window, message):
        """Append a timestamped status message to the current window.

        Parameters
        ----------
        window : sg.Window
            Window instance receiving the message.
        message : str
            Message to append to the log panel.
        """
        window["-message-"].update(
            append_note(message, window["-message-"].get())
        )

    def _refresh(self, window, credentials=None):
        """Refresh the list of credential rows shown to the user.

        Parameters
        ----------
        window : sg.Window
            Window whose credential list should be updated.
        credentials : list, optional
            Optional filtered credential list. If omitted, all user credentials are
            loaded.
        """
        credentials = credentials if credentials is not None else self.vault.list(self.user_id)
        self.credentials = list(credentials)
        rows = [
            [c.application, c.username, c.time_modified, c.date_modified]
            for c in self.credentials
        ]
        window["-list-"].update(values=rows)

    def _clear(self, window):
        """Clear the form fields and deselect the active credential.

        Parameters
        ----------
        window : sg.Window
            Window whose input values should be reset.
        """
        for key in ("-app-", "-user-", "-pass-", "-comment-"):
            window[key].update("")
        self.selected = None

    def run(self):
        """Open the main password manager interface and handle user actions.

        Returns
        -------
        None
            Displays the manager until the user exits the window.
        """
        window = sg.Window(
            "Password Manager",
            self._layout(),
            size=(1200, 760),
            finalize=True,
            background_color=THEME["bg"],
            resizable=True,
        )
        self._refresh(window)

        try:
            while True:
                event, values = window.read()

                if event in (sg.WIN_CLOSED, "Exit"):
                    return

                if event == "-list-" and values["-list-"]:
                    credential_index = values["-list-"][0]
                    credential_row = self.credentials[credential_index]
                    app, username = credential_row.application, credential_row.username
                    try:
                        credential = self.vault.get(self.user_id, app, username)
                        self.selected = (app, username)
                        window["-app-"].update(credential.application)
                        window["-user-"].update(credential.username)
                        window["-pass-"].update(credential.password)
                        window["-comment-"].update(credential.comment)
                    except CredentialNotFoundError as exc:
                        self._message(window, str(exc))

                elif event == "Help":
                    generated = PasswordHelperView(
                        self.generator, self.breach_checker
                    ).run()
                    if generated:
                        window["-pass-"].update(generated)

                elif event == "Add":
                    try:
                        self.vault.add(
                            self.user_id,
                            values["-app-"],
                            values["-user-"],
                            values["-pass-"],
                            values["-comment-"],
                        )
                        self._refresh(window)
                        self._clear(window)
                        self._message(window, "Successfully Added!")
                    except (ValueError, DuplicateCredentialError) as exc:
                        self._message(window, str(exc))

                elif event == "Search":
                    self._refresh(
                        window,
                        self.vault.search(
                            self.user_id,
                            values["-app-"],
                            values["-user-"],
                        ),
                    )

                elif event == "Update":
                    if not self.selected:
                        self._message(window, "Select a credential first.")
                        continue

                    app, username = self.selected
                    if (values["-app-"], values["-user-"]) != (app, username):
                        self._message(window, "Application and username cannot be renamed.")
                        continue

                    old = self.vault.get(self.user_id, app, username)
                    changed = old.password != values["-pass-"]

                    if changed:
                        answer = sg.popup_yes_no(
                            "The current password and key will be replaced. Continue?",
                            title="Update Password",
                            keep_on_top=True,
                        )
                        if answer != "Yes":
                            continue

                    self.vault.update(
                        self.user_id,
                        app,
                        username,
                        values["-pass-"],
                        values["-comment-"],
                        changed,
                    )
                    self._refresh(window)
                    self._message(
                        window,
                        "Password was updated!" if changed else "Comment was updated!",
                    )

                elif event == "Delete":
                    if not self.selected:
                        self._message(window, "Select a credential first.")
                        continue

                    answer = sg.popup_yes_no(
                        "You are about to permanently delete this credential. Continue?",
                        title="Delete an item",
                        keep_on_top=True,
                    )
                    if answer == "Yes":
                        app, username = self.selected
                        self.vault.delete(self.user_id, app, username)
                        self._refresh(window)
                        self._clear(window)
                        self._message(window, "Item Deleted!")

                elif event == "Change Master Password":
                    self._change_master_password(window)

                elif event == "Create PDF":
                    try:
                        master = self.auth.master_password(self.user_id)
                        path = self.pdf_exporter.export(
                            self.vault.list(self.user_id),
                            master,
                        )
                        self._message(window, f"PDF created: {path}")
                    except Exception as exc:
                        self._message(window, f"PDF creation failed: {exc}")

        finally:
            window.close()

    def _change_master_password(self, parent):
        """Open a modal dialog to update the current user's master password."""
        layout = [
            [sg.Text("Current"), input_style("-current-", password=True)],
            [sg.Text("New"), input_style("-new1-", password=True)],
            [sg.Text("Repeat"), input_style("-new2-", password=True)],
            [button_style("Generate", "secondary"), button_style("Submit", "primary"), button_style("Exit", "danger")],
            [sg.Text("", key="-error-", size=(50, 2), text_color="red")],
        ]

        dialog = sg.Window(
            "Change Master Password", layout, modal=True, finalize=True
        )
        try:
            while True:
                event, values = dialog.read()
                if event in (sg.WIN_CLOSED, "Exit"):
                    return

                if event == "Generate":
                    generated = PasswordHelperView(
                        self.generator, self.breach_checker
                    ).run()
                    if generated:
                        dialog["-new1-"].update(generated)

                elif event == "Submit":
                    current = values["-current-"]
                    new1 = values["-new1-"]
                    new2 = values["-new2-"]

                    if not all((current, new1, new2)):
                        dialog["-error-"].update("All fields are required.")
                        continue
                    if new1 != new2:
                        dialog["-error-"].update("New passwords do not match.")
                        continue

                    try:
                        self.auth.change_master_password(
                            self.user_id, current, new1
                        )
                    except Exception as exc:
                        dialog["-error-"].update(str(exc))
                        continue

                    sg.popup_ok("Successfully Changed")
                    return
        finally:
            dialog.close()
