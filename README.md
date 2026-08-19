# Password Manager — OOP Refactor

A clean OOP refactor of the original `avivfaraj/password-manager`.

## Architecture

- `models.py` — domain objects
- `utilities.py` — small stateless helpers
- `crypto.py` — Fernet encryption
- `password_generator.py` — secure password generation
- `breach_checker.py` — Have I Been Pwned client
- `repositories.py` — SQLite persistence
- `services.py` — application/business logic
- `pdf_exporter.py` — password-protected PDF export
- `gui/` — PySimpleGUI presentation layer
- `app.py` — application entry point

The GUI is kept at the edge. Business logic does not depend on PySimpleGUI.

## Compatibility

The original project uses two SQLite databases (`keys.db` and `hash.db`). This refactor preserves that schema so existing databases can be opened.

**Back up your databases before migrating.**

## Run

```bash
pip install -r requirements.txt
python run.py
```

## Security note

The original storage design encrypts the master password with a Fernet key stored in the companion database. This refactor preserves that model for compatibility; it does not claim to be a modern zero-knowledge vault format.

HIBP uses the k-anonymity range API: only the first five SHA-1 characters of a password hash are sent.
