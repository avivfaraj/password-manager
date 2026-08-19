from password_manager.crypto import EncryptionError
from password_manager.models import Credential
from password_manager.repositories import VaultRepositories


class AuthenticationError(Exception):
    """Exception raised when authentication fails.

    This can happen when a username is invalid, the stored password cannot be
    decrypted, or the master password does not match the stored record.
    """


class DuplicateCredentialError(Exception):
    """Exception raised when a credential already exists in the vault."""


class CredentialNotFoundError(Exception):
    """Exception raised when a requested credential is missing."""


class AuthenticationService:
    """Handle user registration and master-password authentication.

    Parameters
    ----------
    repositories : VaultRepositories
        Data repositories for user and credential records.
    crypto : EncryptionService
        Encryption service used to protect user credentials.
    """

    def __init__(self, repositories, crypto):
        """Initialize the authentication service.

        Parameters
        ----------
        repositories : VaultRepositories
            Database repositories for the password vault.
        crypto : EncryptionService
            Encryption helper used for password storage and validation.
        """
        self.repositories = repositories
        self.crypto = crypto

    def register(self, username, password):
        """Register a new user account.

        Parameters
        ----------
        username : str
            User name to register.
        password : str
            Master password for the user account.

        Returns
        -------
        int
            User id assigned to the new account.

        Raises
        ------
        ValueError
            If either argument is missing.
        AuthenticationError
            If the username already exists or the two databases become inconsistent.
        """
        if not username or not password:
            raise ValueError("Username and password are required")
        if self.repositories.hashes.find_user(username=username):
            raise AuthenticationError("Username already exists")

        key = self.crypto.generate_key()
        ciphertext = self.crypto.encrypt(password, key)[1]
        hash_id = self.repositories.hashes.add_user(username, ciphertext)
        key_id = self.repositories.keys.add_user(username, key)

        if hash_id != key_id:
            raise AuthenticationError("The two databases became inconsistent")
        return hash_id

    def authenticate(self, username, password):
        """Authenticate an existing user.

        Parameters
        ----------
        username : str
            User name to validate.
        password : str
            Master password supplied by the user.

        Returns
        -------
        int
            User id for the authenticated account.

        Raises
        ------
        AuthenticationError
            If the username or password is incorrect or the stored data cannot be
            decrypted.
        """
        hashes = self.repositories.hashes.find_user(username=username)
        keys = self.repositories.keys.find_user(username=username)

        if not hashes or not keys or hashes[0][0] != keys[0][0] or hashes[0][1] != keys[0][1]:
            raise AuthenticationError("Username and/or password are incorrect")

        try:
            stored = self.crypto.decrypt(keys[0][2], hashes[0][2])
        except EncryptionError as exc:
            raise AuthenticationError("Stored credentials cannot be decrypted") from exc

        if stored != password:
            raise AuthenticationError("Username and/or password are incorrect")
        return int(keys[0][0])

    def change_master_password(self, user_id, current, new):
        """Change the user's master password.

        Parameters
        ----------
        user_id : int
            User whose master password should change.
        current : str
            Current master password.
        new : str
            Replacement master password.

        Raises
        ------
        AuthenticationError
            If the user does not exist or the current password is invalid.
        """
        hashes = self.repositories.hashes.find_user(user_id=user_id)
        keys = self.repositories.keys.find_user(user_id=user_id)
        if not hashes or not keys:
            raise AuthenticationError("User not found")

        if self.crypto.decrypt(keys[0][2], hashes[0][2]) != current:
            raise AuthenticationError("Invalid Password")

        new_key = self.crypto.generate_key()
        new_ciphertext = self.crypto.encrypt(new, new_key)[1]
        self.repositories.keys.update_user_password(user_id, new_key)
        self.repositories.hashes.update_user_password(user_id, new_ciphertext)

    def master_password(self, user_id):
        """Retrieve the decrypted master password for a user.

        Parameters
        ----------
        user_id : int
            User id to query.

        Returns
        -------
        str
            Decrypted master password.

        Raises
        ------
        AuthenticationError
            If the user cannot be found.
        """
        hashes = self.repositories.hashes.find_user(user_id=user_id)
        keys = self.repositories.keys.find_user(user_id=user_id)
        if not hashes or not keys:
            raise AuthenticationError("User not found")
        return self.crypto.decrypt(keys[0][2], hashes[0][2])


class VaultService:
    """Manage encrypted credentials in the user's vault.

    Parameters
    ----------
    repositories : VaultRepositories
        Repository bundle that stores key and hash data.
    crypto : EncryptionService
        Cryptographic helper used to encrypt and decrypt payloads.
    """

    def __init__(self, repositories, crypto):
        """Initialize the vault service.

        Parameters
        ----------
        repositories : VaultRepositories
            Repository bundle for the user's data stores.
        crypto : EncryptionService
            Encryption and decryption service.
        """
        self.repositories = repositories
        self.crypto = crypto

    def _from_row(self, row, key):
        """Create a credential object from the database data.

        Parameters
        ----------
        row : tuple
            Credential row returned by the hash repository.
        key : bytes
            Encryption key used to decrypt the stored password.

        Returns
        -------
        Credential
            Fully hydrated credential object.

        Raises
        ------
        EncryptionError
            If the key and stored payload cannot be decrypted.
        """
        return Credential(
            application=row[2],
            username=row[3],
            password=self.crypto.decrypt(key, row[4]),
            comment=row[5],
            time_modified=row[7],
            date_modified=row[6],
        )

    def list(self, user_id):
        """List all readable credentials for a user.

        Parameters
        ----------
        user_id : int
            User id to query.

        Returns
        -------
        list[Credential]
            Credentials readable from the vault for the user.
        """
        key_rows = self.repositories.keys.list_keys(user_id)
        key_map = {(row[2], row[3]): row[4] for row in key_rows}
        result = []
        for row in self.repositories.hashes.list_credentials(user_id):
            key = key_map.get((row[2], row[3]))
            if key:
                try:
                    result.append(self._from_row(row, key))
                except EncryptionError:
                    pass
        return result

    def get(self, user_id, application, username):
        """Fetch a single credential by application and username.

        Parameters
        ----------
        user_id : int
            User id that owns the credential.
        application : str
            Application name.
        username : str
            Username tied to the credential.

        Returns
        -------
        Credential
            Matching credential object.

        Raises
        ------
        CredentialNotFoundError
            If the credential does not exist.
        """
        hashes = self.repositories.hashes.find_exact(user_id, application, username)
        keys = self.repositories.keys.find_key(user_id, application, username)
        if not hashes or not keys:
            raise CredentialNotFoundError("Credential not found")
        return self._from_row(hashes[0], keys[0][4])

    def search(self, user_id, application, username=""):
        """Search for credentials matching an app and optional username.

        Parameters
        ----------
        user_id : int
            User id to search within.
        application : str
            Application prefix to match.
        username : str, optional
            Username prefix to match. The default is ``""``.

        Returns
        -------
        list[Credential]
            Matching credentials that can be decrypted successfully.
        """
        result = []
        for row in self.repositories.hashes.find_credentials(user_id, application, username):
            keys = self.repositories.keys.find_key(user_id, row[2], row[3])
            if keys:
                try:
                    result.append(self._from_row(row, keys[0][4]))
                except EncryptionError:
                    pass
        return result

    def add(self, user_id, application, username, password, comment):
        """Add a new credential to the vault.

        Parameters
        ----------
        user_id : int
            User id that owns the new credential.
        application : str
            Application name.
        username : str
            Username to store.
        password : str
            Password for the application.
        comment : str
            Notes about the credential.

        Raises
        ------
        ValueError
            If any required credential field is empty.
        DuplicateCredentialError
            If the credential already exists for the user.
        """
        if not all((application, username, password)):
            raise ValueError("Application, username and password are required")
        if self.repositories.hashes.find_exact(user_id, application, username):
            raise DuplicateCredentialError("That credential already exists")

        key, ciphertext = self.crypto.encrypt(password)
        self.repositories.hashes.add_credential(
            user_id, application, username, ciphertext, comment
        )
        self.repositories.keys.add_key(user_id, application, username, key)

    def update(self, user_id, application, username, password, comment, password_changed):
        """Update an existing credential in the vault.

        Parameters
        ----------
        user_id : int
            User id that owns the credential.
        application : str
            Application name.
        username : str
            Username for the credential.
        password : str
            New password value.
        comment : str
            Updated comment text.
        password_changed : bool
            Indicates whether the password was updated.

        Raises
        ------
        CredentialNotFoundError
            If the credential does not exist.
        """
        if not self.repositories.hashes.find_exact(user_id, application, username):
            raise CredentialNotFoundError("Credential not found")

        if password_changed:
            key, ciphertext = self.crypto.encrypt(password)
            self.repositories.hashes.update_credential(
                user_id, application, username, ciphertext, comment
            )
            self.repositories.keys.update_key(
                user_id, application, username, key
            )
        else:
            self.repositories.hashes.update_comment(
                user_id, application, username, comment
            )

    def delete(self, user_id, application, username):
        """Delete a credential and its key entry.

        Parameters
        ----------
        user_id : int
            User id that owns the credential.
        application : str
            Application name.
        username : str
            Username for the credential.

        Raises
        ------
        CredentialNotFoundError
            If the credential is missing.
        """
        if not self.repositories.hashes.find_exact(user_id, application, username):
            raise CredentialNotFoundError("Credential not found")
        self.repositories.hashes.delete_credential(user_id, application, username)
        self.repositories.keys.delete_key(user_id, application, username)
