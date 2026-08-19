import hashlib
import requests


class BreachCheckError(Exception):
    """Exception raised when a password-breach check fails.

    This error is raised when the HIBP API cannot be reached or the response
    cannot be parsed successfully.
    """


class HIBPClient:
    """Client used to query the Have I Been Pwned password API.

    Attributes
    ----------
    API_URL : str
        API endpoint format used to retrieve password breach ranges.
    timeout : float
        Timeout in seconds for HTTP requests.
    session : requests.Session
        HTTP session used to make outbound requests.
    """

    API_URL = "https://api.pwnedpasswords.com/range/{}"

    def __init__(self, timeout: float = 10.0, session=None):
        """Initialize the client.

        Parameters
        ----------
        timeout : float, optional
            Timeout value in seconds for network requests. The default is 10.0.
        session : requests.Session, optional
            Optional HTTP session to reuse. If not provided, a new session is made.
        """
        self.timeout = timeout
        self.session = session or requests.Session()

    def count(self, password: str) -> int:
        """Count how many times the password appears in public breach data.

        Parameters
        ----------
        password : str
            Plain-text password to check.

        Returns
        -------
        int
            Number of times the password was observed in breaches.

        Raises
        ------
        BreachCheckError
            If the password-check request cannot complete because the API is
            unavailable or the response is invalid.
        """
        digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix, suffix = digest[:5], digest[5:]

        try:
            response = self.session.get(
                self.API_URL.format(prefix),
                headers={"Add-Padding": "true"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise BreachCheckError("Unable to reach Have I Been Pwned") from exc

        for line in response.text.splitlines():
            parts = line.split(":")
            if len(parts) == 2 and parts[0].upper() == suffix:
                try:
                    return int(parts[1])
                except ValueError:
                    return 0
        return 0
