import os
import PySimpleGUI as sg

from password_manager.services import CredentialNotFoundError, DuplicateCredentialError
from password_manager.utilities import append_note
from password_manager.gui.common import PasswordHelperView


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

    def _layout(self):
        """Create the main layout of the manager window.

        Returns
        -------
        list
            PySimpleGUI layout definition for the manager form and listbox.
        """
        return [
            [sg.Frame("Credential", [
                [sg.Text("Application"), sg.Input(key="-app-", size=(30, 1))],
                [sg.Text("Username"), sg.Input(key="-user-", size=(30, 1))],
                [sg.Text("Password"), sg.Input(key="-pass-", size=(30, 1)), sg.Button("Help")],
                [sg.Text("Comment"), sg.Multiline(key="-comment-", size=(30, 4))],
                [sg.Button("Add"), sg.Button("Update"), sg.Button("Delete"), sg.Button("Search")],
            ])],
            [
                sg.Listbox([], size=(45, 20), enable_events=True, key="-list-"),
                sg.Multiline(size=(45, 20), key="-message-", disabled=True),
            ],
            [sg.Button("Change Master Password"), sg.Button("Create PDF"), sg.Button("Exit")],
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
        window["-list-"].update([
            [c.application, c.username, c.time_modified, c.date_modified]
            for c in credentials
        ])

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
            size=(950, 650),
            finalize=True,
        )
        self._refresh(window)

        try:
            while True:
                event, values = window.read()

                if event in (sg.WIN_CLOSED, "Exit"):
                    return

                if event == "-list-" and values["-list-"]:
                    app, username = values["-list-"][0][:2]
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
                            os.path.join(os.getcwd(), "password.pdf"),
                        )
                        self._message(window, f"PDF created: {path}")
                    except Exception as exc:
                        self._message(window, f"PDF creation failed: {exc}")

        finally:
            window.close()

    def _change_master_password(self, parent):
        """Open a modal dialog to update the current user's master password."""
        layout = [
            [sg.Text("Current"), sg.Input(password_char="*", key="-current-")],
            [sg.Text("New"), sg.Input(password_char="*", key="-new1-")],
            [sg.Text("Repeat"), sg.Input(password_char="*", key="-new2-")],
            [sg.Button("Generate"), sg.Button("Submit"), sg.Button("Exit")],
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
