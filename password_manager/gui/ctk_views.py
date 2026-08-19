import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from password_manager.breach_checker import BreachCheckError
from password_manager.password_generator import PasswordPolicy
from password_manager.services import AuthenticationError
from password_manager.utilities import append_note, build_database_path, is_sqlite_path


COLORS = {
    "bg": "#0b1220",
    "panel": "#111b2e",
    "panel_alt": "#1b2b43",
    "field": "#223652",
    "field_border": "#5879a2",
    "text": "#eef4ff",
    "muted": "#9eb0c9",
    "accent": "#5b8def",
    "accent_hover": "#79a2f5",
    "success": "#34d399",
    "success_hover": "#62e6b0",
    "danger": "#f87171",
    "danger_hover": "#ff9696",
    "warning": "#fbbf24",
    "warning_hover": "#ffd66b",
}


def configure_window(window, title, geometry, parent=None):
    window.title(title)
    window.geometry(geometry)
    window.configure(fg_color=COLORS["bg"])
    window.minsize(720, 520)
    if parent is not None:
        window.transient(parent)
        window.grab_set()
    window.deiconify()
    window.lift()
    window.focus_force()


def make_label(parent, text, size=11, bold=False, color=None):
    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=color or COLORS["text"],
        font=("Segoe UI", size, "bold" if bold else "normal"),
    )


def make_entry(parent, variable=None, password=False, width=320):
    return ctk.CTkEntry(
        parent,
        width=width,
        height=42,
        textvariable=variable,
        show="*" if password else "",
        fg_color=COLORS["field"],
        border_color=COLORS["field_border"],
        border_width=1,
        text_color=COLORS["text"],
        placeholder_text_color=COLORS["muted"],
        corner_radius=10,
        font=("Segoe UI", 12),
    )


def make_button(parent, text, command, variant="secondary", width=120):
    colors = {
        "primary": (COLORS["accent"], COLORS["accent_hover"]),
        "secondary": (COLORS["panel_alt"], COLORS["field_border"]),
        "success": (COLORS["success"], COLORS["success_hover"]),
        "danger": (COLORS["danger"], COLORS["danger_hover"]),
        "warning": (COLORS["warning"], COLORS["warning_hover"]),
    }
    foreground, hover = colors[variant]
    text_color = COLORS["bg"] if variant in ("success", "warning") else COLORS["text"]
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=40,
        corner_radius=12,
        fg_color=foreground,
        hover_color=hover,
        text_color=text_color,
        font=("Segoe UI", 11, "bold"),
    )


def make_panel(parent, **grid_options):
    panel = ctk.CTkFrame(
        parent,
        fg_color=COLORS["panel"],
        corner_radius=16,
        border_width=1,
        border_color="#263b59",
    )
    panel.grid(**grid_options)
    return panel


def set_textbox(textbox, value, disabled=False):
    textbox.configure(state="normal")
    textbox.delete("1.0", "end")
    textbox.insert("1.0", value)
    if disabled:
        textbox.configure(state="disabled")


class PasswordHelperView:
    def __init__(self, generator, breach_checker):
        self.generator = generator
        self.breach_checker = breach_checker
        self.result = ""

    def run(self, parent=None):
        owns_root = parent is None
        if owns_root:
            parent = ctk.CTk()
            parent.withdraw()
        window = ctk.CTkToplevel(parent)
        configure_window(window, "Password Helper", "700x650", parent)
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        window.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(window, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=30, pady=24)
        content.grid_columnconfigure(1, weight=1)
        make_label(content, "Password generator", 24, True).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 24))

        sliders = (("Digits", "digits", 4), ("Letters", "letters", 8), ("Symbols", "symbols", 4))
        values = {}
        for row, (label, key, default) in enumerate(sliders, 1):
            make_label(content, label, 11, True, COLORS["muted"]).grid(row=row, column=0, sticky="w", pady=10)
            values[key] = tk.IntVar(value=default)
            slider = ctk.CTkSlider(
                content,
                from_=0,
                to=20,
                variable=values[key],
                number_of_steps=20,
                progress_color=COLORS["accent"],
                button_color=COLORS["accent_hover"],
                button_hover_color=COLORS["text"],
            )
            slider.grid(row=row, column=1, sticky="ew", padx=(22, 12), pady=10)
            ctk.CTkLabel(content, textvariable=values[key], width=30, text_color=COLORS["text"]).grid(row=row, column=2)

        password = tk.StringVar()
        make_label(content, "Password", 11, True, COLORS["muted"]).grid(row=4, column=0, sticky="w", pady=(18, 6))
        make_entry(content, password, width=430).grid(row=4, column=1, columnspan=2, sticky="ew", pady=(18, 6))

        message = ctk.CTkTextbox(content, height=150, fg_color=COLORS["field"], border_color=COLORS["field_border"], border_width=1, corner_radius=10, text_color=COLORS["text"], font=("Segoe UI", 11))
        message.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=(22, 18))
        content.grid_rowconfigure(5, weight=1)

        def add_message(text):
            current = message.get("1.0", "end").strip()
            set_textbox(message, append_note(text, current))

        def generate():
            generated = self.generator.generate(PasswordPolicy(letters=values["letters"].get(), digits=values["digits"].get(), symbols=values["symbols"].get()))
            password.set(generated)
            add_message("Password generated." + (" More than 8 characters is recommended." if len(generated) < 8 else ""))

        def check_password():
            current = password.get()
            if not current:
                add_message("Please enter password!")
                return
            try:
                count = self.breach_checker.count(current)
                add_message(f"Password was leaked! It appears {count} times in the database." if count else self.generator.strength_message(current))
            except BreachCheckError:
                add_message("Error: No internet connection or HIBP is unavailable.")

        def use_password():
            self.result = password.get()
            window.destroy()

        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.grid(row=6, column=0, columnspan=3, sticky="ew")
        for column in range(4):
            actions.grid_columnconfigure(column, weight=1)
        make_button(actions, "Generate", generate, "primary", 140).grid(row=0, column=0, padx=4)
        make_button(actions, "Check password", check_password, "secondary", 150).grid(row=0, column=1, padx=4)
        make_button(actions, "Use", use_password, "success", 100).grid(row=0, column=2, padx=4)
        make_button(actions, "Exit", window.destroy, "danger", 100).grid(row=0, column=3, padx=4)

        window.wait_window()
        if owns_root:
            parent.destroy()
        return self.result


class LoginView:
    def __init__(self, crypto, generator, breach_checker, pdf_exporter):
        self.crypto = crypto
        self.generator = generator
        self.breach_checker = breach_checker
        self.pdf_exporter = pdf_exporter

    def run(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        root = ctk.CTk()
        configure_window(root, "Log In", "980x650")
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        hero = make_panel(root, row=0, column=0, sticky="nsew", padx=(24, 12), pady=24)
        hero.configure(fg_color=COLORS["panel_alt"])
        hero.grid_columnconfigure(0, weight=1)
        make_label(hero, "VaultGuard", 34, True).grid(row=0, column=0, sticky="w", padx=32, pady=(50, 8))
        make_label(hero, "Secure password management", 15, False, COLORS["muted"]).grid(row=1, column=0, sticky="w", padx=32)
        make_label(hero, "Your vault is protected by end-to-end encryption and secure key storage.", 12, False, COLORS["muted"],).grid(row=2, column=0, sticky="w", padx=32, pady=(28, 0))
        ctk.CTkFrame(hero, height=4, fg_color=COLORS["accent"], corner_radius=2).grid(row=3, column=0, sticky="ew", padx=32, pady=(28, 0))

        form = make_panel(root, row=0, column=1, sticky="nsew", padx=(12, 24), pady=24)
        form.grid_columnconfigure(0, weight=1)
        make_label(form, "Welcome back", 28, True).grid(row=0, column=0, sticky="w", padx=34, pady=(38, 28))
        entries = {}
        fields = (("Hash database", "hash", False), ("Key database", "keys", False), ("Username", "user", False), ("Password", "pass", True))
        for row, (label, key, secret) in enumerate(fields, 1):
            make_label(form, label, 11, True, COLORS["muted"]).grid(row=row * 2 - 1, column=0, sticky="w", padx=34, pady=(8, 5))
            line = ctk.CTkFrame(form, fg_color="transparent")
            line.grid(row=row * 2, column=0, sticky="ew", padx=34)
            line.grid_columnconfigure(0, weight=1)
            entries[key] = make_entry(line, password=secret, width=420)
            entries[key].grid(row=0, column=0, sticky="ew")
            if key in ("hash", "keys"):
                make_button(line, "Browse", lambda key=key: self._browse_file(entries[key]), "secondary", 92).grid(row=0, column=1, padx=(10, 0))

        error = make_label(form, "", 11, False, COLORS["danger"])
        error.grid(row=9, column=0, sticky="w", padx=34, pady=(14, 8))
        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.grid(row=10, column=0, sticky="ew", padx=30, pady=(8, 24))
        make_button(actions, "Register", lambda: self._register(root), "secondary", 120).pack(side="left", padx=4)
        make_button(actions, "Log in", lambda: self._login(root, entries, error), "primary", 120).pack(side="left", padx=4)
        make_button(actions, "Exit", root.destroy, "danger", 100).pack(side="left", padx=4)
        self.entries = entries
        self.error = error
        root.mainloop()

    @staticmethod
    def _browse_file(entry):
        path = filedialog.askopenfilename(filetypes=[("SQLite database", "*.db"), ("All files", "*.*")])
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _register(self, root):
        root.withdraw()
        try:
            RegisterView(self.generator, self.breach_checker, self.crypto).run(root)
        finally:
            root.deiconify()

    def _login(self, root, entries, error):
        keys_path, hash_path = entries["keys"].get(), entries["hash"].get()
        username, password = entries["user"].get(), entries["pass"].get()
        if not all((keys_path, hash_path, username, password)):
            error.configure(text="All fields are required.")
            return
        if not is_sqlite_path(keys_path) or not is_sqlite_path(hash_path):
            error.configure(text="Database files must use the .db extension.")
            return
        try:
            from password_manager.app import create_services
            repositories, auth, vault = create_services(keys_path, hash_path)
            user_id = auth.authenticate(username, password)
        except AuthenticationError as exc:
            error.configure(text=str(exc))
            return
        except Exception as exc:
            error.configure(text=f"Unable to open databases: {exc}")
            return
        root.withdraw()
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
        except Exception as exc:
            root.deiconify()
            messagebox.showerror("Unable to open vault", str(exc), parent=root)
        finally:
            repositories.close()
            root.deiconify()


class RegisterView:
    def __init__(self, generator, breach_checker, crypto):
        self.generator = generator
        self.breach_checker = breach_checker
        self.crypto = crypto
        self.result = False

    def run(self):
        owns_root = parent is None
        if owns_root:
            parent = ctk.CTk()
            parent.withdraw()
        window = ctk.CTkToplevel(parent)
        configure_window(window, "Register", "820x650", parent)
        window.grid_columnconfigure(0, weight=1)
        form = make_panel(window, row=0, column=0, sticky="nsew", padx=28, pady=28)
        form.grid_columnconfigure(0, weight=1)
        make_label(form, "Create your vault", 28, True).grid(row=0, column=0, sticky="w", padx=36, pady=(32, 6))
        make_label(form, "Choose where the encrypted databases will live.", 12, False, COLORS["muted"]).grid(row=1, column=0, sticky="w", padx=36, pady=(0, 24))
        entries = {}
        fields = (("Hash database directory", "hash_dir"), ("Key database directory", "keys_dir"), ("Username", "user"), ("Password", "pass"))
        for row, (label, key) in enumerate(fields):
            make_label(form, label, 11, True, COLORS["muted"]).grid(row=row * 2 + 2, column=0, sticky="w", padx=36, pady=(8, 5))
            line = ctk.CTkFrame(form, fg_color="transparent")
            line.grid(row=row * 2 + 3, column=0, sticky="ew", padx=36)
            line.grid_columnconfigure(0, weight=1)
            entries[key] = make_entry(line, password=key == "pass", width=500)
            entries[key].grid(row=0, column=0, sticky="ew")
            if key.endswith("dir"):
                make_button(line, "Browse", lambda key=key: self._browse_directory(entries[key]), "secondary", 92).grid(row=0, column=1, padx=(10, 0))
        error = make_label(form, "", 11, False, COLORS["danger"])
        error.grid(row=10, column=0, sticky="w", padx=36, pady=(14, 8))
        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.grid(row=11, column=0, sticky="w", padx=32, pady=(8, 28))
        make_button(actions, "Help", lambda: self._help(window, entries["pass"]), "warning", 100).pack(side="left", padx=4)
        make_button(actions, "Register", lambda: self._submit(window, entries, error), "success", 120).pack(side="left", padx=4)
        make_button(actions, "Exit", window.destroy, "danger", 100).pack(side="left", padx=4)
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        window.wait_window()
        if owns_root:
            parent.destroy()
        return self.result

    @staticmethod
    def _browse_directory(entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _help(self, window, entry):
        generated = PasswordHelperView(self.generator, self.breach_checker).run(window)
        if generated:
            entry.delete(0, "end")
            entry.insert(0, generated)

    def _submit(self, window, entries, error):
        required = [entries[key].get() for key in ("hash_dir", "keys_dir", "user", "pass")]
        if not all(required):
            error.configure(text="All fields are required.")
            return
        hash_path = build_database_path(entries["hash_dir"].get(), "hash.db")
        keys_path = build_database_path(entries["keys_dir"].get(), "keys.db")
        try:
            from password_manager.app import create_services
            repositories, auth, _ = create_services(keys_path, hash_path)
            try:
                auth.register(entries["user"].get(), entries["pass"].get())
            finally:
                repositories.close()
        except AuthenticationError as exc:
            error.configure(text=str(exc))
            return
        except Exception as exc:
            error.configure(text=f"Registration failed: {exc}")
            return
        messagebox.showinfo("Registration successful", "Your encrypted vault is ready.", parent=window)
        self.result = True
        window.destroy()


class ManagerView:
    def __init__(self, user_id, auth, vault, repositories, generator, breach_checker, pdf_exporter):
        self.user_id = user_id
        self.auth = auth
        self.vault = vault
        self.repositories = repositories
        self.generator = generator
        self.breach_checker = breach_checker
        self.pdf_exporter = pdf_exporter
        self.selected = None
        self.credentials = []

    def run(self, parent=None):
        window = ctk.CTkToplevel()
        self.window = window
        configure_window(window, "Password Manager", "1200x900")
        window.minsize(1240, 760)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=1)
        window.grid_rowconfigure(0, minsize=72)
        window.grid_rowconfigure(1, minsize=420, weight=1)
        window.grid_rowconfigure(2, minsize=150, weight=0)
        window.grid_rowconfigure(3, minsize=58, weight=0)
        make_label(window, "Vault dashboard", 28, True).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 14))
        make_label(window, "Secure workspace", 12, False, COLORS["muted"]).grid(row=0, column=1, sticky="e", padx=28, pady=(24, 14))

        list_panel = make_panel(window, row=1, column=0, sticky="nsew", padx=(24, 12), pady=(0, 12))
        list_panel.grid_rowconfigure(1, weight=1)
        list_panel.grid_columnconfigure(0, weight=1)
        make_label(list_panel, "Credentials", 18, True).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 12))
        table_frame = ctk.CTkFrame(list_panel, fg_color=COLORS["field"], corner_radius=10)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        style = ttk.Style(window)
        style.theme_use("clam")
        style.configure("Vault.Treeview", background=COLORS["field"], foreground=COLORS["text"], fieldbackground=COLORS["field"], rowheight=32, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Vault.Treeview.Heading", background=COLORS["panel_alt"], foreground=COLORS["text"], relief="flat", font=("Segoe UI", 10, "bold"))
        style.map("Vault.Treeview", background=[("selected", COLORS["accent"])], foreground=[("selected", COLORS["text"])])
        self.table = ttk.Treeview(table_frame, columns=("application", "username", "modified", "date"), show="headings", style="Vault.Treeview", selectmode="browse")
        for key, heading, width in (("application", "Application", 190), ("username", "Username", 170), ("modified", "Last changed", 120), ("date", "Date", 100)):
            self.table.heading(key, text=heading)
            self.table.column(key, width=width, anchor="w", stretch=True)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.bind("<<TreeviewSelect>>", self._select_credential)
        make_button(list_panel, "Search", self._search, "secondary", 120).grid(row=2, column=0, sticky="w", padx=18, pady=(0, 18))

        form_panel = ctk.CTkScrollableFrame(
            window,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color="#263b59",
        )
        form_panel.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=(0, 12))
        form_panel.grid_columnconfigure(0, weight=1)
        form_panel._scrollbar.grid_remove()

        def update_form_scrollbar(_event=None):
            if window.winfo_height() < 820:
                form_panel._scrollbar.grid()
            else:
                form_panel._scrollbar.grid_remove()

        window.bind("<Configure>", update_form_scrollbar)
        window.after_idle(update_form_scrollbar)
        make_label(form_panel, "Credential details", 18, True).grid(row=0, column=0, sticky="w", padx=24, pady=(18, 14))
        self.form_entries = {}
        for row, label in enumerate(("Application", "Username"), 1):
            make_label(form_panel, label, 11, True, COLORS["muted"]).grid(row=row * 2 - 1, column=0, sticky="w", padx=24, pady=(8, 5))
            self.form_entries[label.lower()] = make_entry(form_panel, width=400)
            self.form_entries[label.lower()].grid(row=row * 2, column=0, sticky="ew", padx=24)
        password_line = ctk.CTkFrame(form_panel, fg_color="transparent")
        make_label(form_panel, "Password", 11, True, COLORS["muted"]).grid(row=5, column=0, sticky="w", padx=24, pady=(8, 5))
        password_line.grid(row=6, column=0, sticky="ew", padx=24)
        self.form_entries["password"] = make_entry(password_line, width=400)
        self.form_entries["password"].grid(row=0, column=0, sticky="ew")
        password_line.grid_columnconfigure(0, weight=1)
        make_button(password_line, "Help", self._password_help, "warning", 90).grid(row=0, column=1, padx=(10, 0))
        make_label(form_panel, "Comment", 11, True, COLORS["muted"]).grid(row=7, column=0, sticky="w", padx=24, pady=(12, 5))
        self.comment = ctk.CTkTextbox(form_panel, height=115, fg_color=COLORS["field"], border_color=COLORS["field_border"], border_width=1, corner_radius=10, text_color=COLORS["text"], font=("Segoe UI", 11))
        self.comment.grid(row=8, column=0, sticky="ew", padx=24)
        actions = ctk.CTkFrame(form_panel, fg_color="transparent")
        actions.grid(row=9, column=0, sticky="w", padx=20, pady=16)
        make_button(actions, "Add", self._add, "success", 100).pack(side="left", padx=4)
        make_button(actions, "Update", self._update, "primary", 100).pack(side="left", padx=4)
        make_button(actions, "Delete", self._delete, "danger", 100).pack(side="left", padx=4)

        log_panel = make_panel(window, row=2, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 12))
        log_panel.grid_columnconfigure(0, weight=1)
        make_label(log_panel, "Activity log", 16, True).grid(row=0, column=0, sticky="w", padx=20, pady=(12, 5))
        self.message = ctk.CTkTextbox(log_panel, height=105, fg_color=COLORS["field"], border_color=COLORS["field_border"], border_width=1, corner_radius=10, text_color=COLORS["text"], font=("Segoe UI", 10))
        self.message.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))

        footer = ctk.CTkFrame(window, fg_color="transparent")
        footer.grid(row=3, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 18))
        make_button(footer, "Change master password", self._change_master_password, "secondary", 210).pack(side="left", padx=4)
        make_button(footer, "Create PDF", self._create_pdf, "primary", 140).pack(side="left", padx=4)
        make_button(footer, "Exit", window.destroy, "danger", 100).pack(side="left", padx=4)
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        self._refresh()
        window.wait_window()

    def _append_message(self, text):
        current = self.message.get("1.0", "end").strip()
        set_textbox(self.message, append_note(text, current))

    def _refresh(self, credentials=None):
        self.credentials = list(credentials if credentials is not None else self.vault.list(self.user_id))
        for item in self.table.get_children():
            self.table.delete(item)
        for index, credential in enumerate(self.credentials):
            self.table.insert("", "end", iid=str(index), values=(credential.application, credential.username, credential.time_modified, credential.date_modified))

    def _select_credential(self, _event=None):
        selected = self.table.selection()
        if not selected:
            return
        credential = self.credentials[int(selected[0])]
        try:
            credential = self.vault.get(self.user_id, credential.application, credential.username)
            self.selected = (credential.application, credential.username)
            self.form_entries["application"].delete(0, "end")
            self.form_entries["application"].insert(0, credential.application)
            self.form_entries["username"].delete(0, "end")
            self.form_entries["username"].insert(0, credential.username)
            self.form_entries["password"].delete(0, "end")
            self.form_entries["password"].insert(0, credential.password)
            set_textbox(self.comment, credential.comment)
        except Exception as exc:
            self._append_message(str(exc))

    def _clear(self):
        for entry in self.form_entries.values():
            entry.delete(0, "end")
        set_textbox(self.comment, "")
        self.selected = None

    def _search(self):
        self._refresh(self.vault.search(self.user_id, self.form_entries["application"].get(), self.form_entries["username"].get()))

    def _password_help(self):
        generated = PasswordHelperView(self.generator, self.breach_checker).run(self.window)
        if generated:
            self.form_entries["password"].delete(0, "end")
            self.form_entries["password"].insert(0, generated)

    def _add(self):
        try:
            self.vault.add(self.user_id, self.form_entries["application"].get(), self.form_entries["username"].get(), self.form_entries["password"].get(), self.comment.get("1.0", "end").strip())
            self._refresh()
            self._clear()
            self._append_message("Successfully Added!")
        except Exception as exc:
            self._append_message(str(exc))

    def _update(self):
        if not self.selected:
            self._append_message("Select a credential first.")
            return
        app, username = self.selected
        if (self.form_entries["application"].get(), self.form_entries["username"].get()) != (app, username):
            self._append_message("Application and username cannot be renamed.")
            return
        old = self.vault.get(self.user_id, app, username)
        changed = old.password != self.form_entries["password"].get()
        if changed and not messagebox.askyesno("Update password", "The current password and key will be replaced. Continue?", parent=self.window):
            return
        self.vault.update(self.user_id, app, username, self.form_entries["password"].get(), self.comment.get("1.0", "end").strip(), changed)
        self._refresh()
        self._append_message("Password was updated!" if changed else "Comment was updated!")

    def _delete(self):
        if not self.selected:
            self._append_message("Select a credential first.")
            return
        if not messagebox.askyesno("Delete an item", "You are about to permanently delete this credential. Continue?", parent=self.window):
            return
        self.vault.delete(self.user_id, *self.selected)
        self._refresh()
        self._clear()
        self._append_message("Item Deleted!")

    def _create_pdf(self):
        try:
            path = self.pdf_exporter.export(self.vault.list(self.user_id), self.auth.master_password(self.user_id))
            self._append_message(f"PDF created: {path}")
        except Exception as exc:
            self._append_message(f"PDF creation failed: {exc}")

    def _change_master_password(self):
        dialog = ctk.CTkToplevel(self.window)
        configure_window(dialog, "Change Master Password", "520x420", self.window)
        dialog.grid_columnconfigure(0, weight=1)
        panel = make_panel(dialog, row=0, column=0, sticky="nsew", padx=22, pady=22)
        panel.grid_columnconfigure(0, weight=1)
        entries = {}
        for row, (label, key) in enumerate((("Current", "current"), ("New", "new1"), ("Repeat", "new2"))):
            make_label(panel, label, 11, True, COLORS["muted"]).grid(row=row * 2, column=0, sticky="w", padx=22, pady=(10, 5))
            entries[key] = make_entry(panel, password=True, width=400)
            entries[key].grid(row=row * 2 + 1, column=0, sticky="ew", padx=22)
        error = make_label(panel, "", 11, False, COLORS["danger"])
        error.grid(row=6, column=0, sticky="w", padx=22, pady=8)
        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=7, column=0, sticky="w", padx=18, pady=8)
        make_button(actions, "Generate", lambda: self._generate_master(dialog, entries["new1"]), "secondary", 110).pack(side="left", padx=4)
        make_button(actions, "Submit", lambda: self._submit_master(dialog, entries, error), "primary", 100).pack(side="left", padx=4)
        make_button(actions, "Exit", dialog.destroy, "danger", 100).pack(side="left", padx=4)
        dialog.transient(self.window)
        dialog.grab_set()

    def _generate_master(self, dialog, entry):
        generated = PasswordHelperView(self.generator, self.breach_checker).run(dialog)
        if generated:
            entry.delete(0, "end")
            entry.insert(0, generated)

    def _submit_master(self, dialog, entries, error):
        current, new1, new2 = (entries[key].get() for key in ("current", "new1", "new2"))
        if not all((current, new1, new2)):
            error.configure(text="All fields are required.")
            return
        if new1 != new2:
            error.configure(text="New passwords do not match.")
            return
        try:
            self.auth.change_master_password(self.user_id, current, new1)
        except Exception as exc:
            error.configure(text=str(exc))
            return
        messagebox.showinfo("Password changed", "Master password successfully changed.", parent=dialog)
        dialog.destroy()
