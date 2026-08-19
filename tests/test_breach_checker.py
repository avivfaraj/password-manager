"""Tests for password_manager.breach_checker module."""
import pytest
import requests

from password_manager.breach_checker import BreachCheckError, HIBPClient


class FakeSession:
    """Fake requests session for testing."""

    def __init__(self, response_text=None, raise_exception=None):
        """Initialize fake session with response or exception."""
        self.response_text = response_text or ""
        self.raise_exception = raise_exception
        self.last_url = None
        self.last_headers = None
        self.last_timeout = None

    def get(self, url, headers=None, timeout=None):
        """Simulate a GET request."""
        self.last_url = url
        self.last_headers = headers
        self.last_timeout = timeout

        if self.raise_exception:
            raise self.raise_exception

        return FakeResponse(self.response_text)


class FakeResponse:
    """Fake response object for testing."""

    def __init__(self, text=""):
        """Initialize fake response with text."""
        self.text = text

    def raise_for_status(self):
        """Simulate raise_for_status call."""
        pass


class TestHIBPClient:
    """Test cases for the HIBPClient class."""

    def test_client_initialization_with_defaults(self):
        """Test HIBPClient initialization with default values."""
        client = HIBPClient()

        assert client.timeout == 10.0
        assert client.session is not None

    def test_client_initialization_with_custom_timeout(self):
        """Test HIBPClient initialization with custom timeout."""
        client = HIBPClient(timeout=5.0)

        assert client.timeout == 5.0

    def test_client_initialization_with_custom_session(self):
        """Test HIBPClient initialization with custom session."""
        custom_session = FakeSession()
        client = HIBPClient(session=custom_session)

        assert client.session == custom_session

    def test_count_found_in_breaches(self):
        """Test count method returns correct breach count."""
        # SHA1('password') = 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8
        # Prefix: 5BAA6, Suffix: 1E4C9B93F3F0682250B6CF8331B7EE68FD8
        response_text = "1E4C9B93F3F0682250B6CF8331B7EE68FD8:7\nOTHER:2\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(timeout=5.0, session=session)

        count = client.count("password")

        assert count == 7
        assert session.last_url.endswith("5BAA6")  # SHA1 prefix of "password"
        assert session.last_headers["Add-Padding"] == "true"
        assert session.last_timeout == 5.0

    def test_count_not_found_returns_zero(self):
        """Test count returns 0 when password hash not found."""
        response_text = "OTHER:2\nANOTHER:5\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(session=session)

        count = client.count("password")

        assert count == 0

    def test_count_empty_response_returns_zero(self):
        """Test count returns 0 for empty response."""
        session = FakeSession(response_text="")
        client = HIBPClient(session=session)

        count = client.count("password")

        assert count == 0

    def test_count_with_invalid_count_format_returns_zero(self):
        """Test count returns 0 when count value is invalid."""
        response_text = "ABCDEF:not-a-number\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(session=session)

        count = client.count("password")

        assert count == 0

    def test_count_malformed_response_line_skipped(self):
        """Test that malformed lines in response are skipped."""
        response_text = "VALID:5\nMALFORMED_LINE_NO_COLON\nABCDEF:10\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(session=session)

        count = client.count("password")

        # Should find ABCDEF even though there's a malformed line
        assert count == 0  # ABCDEF doesn't match the hash prefix

    def test_count_handles_multiple_colons_in_line(self):
        """Test that lines with multiple colons are handled correctly."""
        response_text = "ABCDEF:7:extra:data\nOTHER:2\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(session=session)

        count = client.count("password")

        # Parts split by ':' will have more than 2 elements, so skipped
        assert count == 0

    def test_count_case_insensitive_matching(self):
        """Test that hash suffix matching is case-insensitive."""
        # SHA1('password') suffix in lowercase
        response_text = "1e4c9b93f3f0682250b6cf8331b7ee68fd8:7\nOTHER:2\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(session=session)

        count = client.count("password")

        # SHA1 produces uppercase, response is lowercase
        # Client should find it due to case-insensitive comparison
        assert count == 7

    def test_count_network_error_raises_breach_check_error(self):
        """Test that network errors raise BreachCheckError."""
        exception = requests.RequestException("Connection refused")
        session = FakeSession(raise_exception=exception)
        client = HIBPClient(session=session)

        with pytest.raises(BreachCheckError, match="Unable to reach Have I Been Pwned"):
            client.count("password")

    def test_count_timeout_raises_breach_check_error(self):
        """Test that connection timeout raises BreachCheckError."""
        exception = requests.Timeout("Request timed out")
        session = FakeSession(raise_exception=exception)
        client = HIBPClient(session=session)

        with pytest.raises(BreachCheckError, match="Unable to reach Have I Been Pwned"):
            client.count("password")

    def test_count_connection_error_raises_breach_check_error(self):
        """Test that connection errors raise BreachCheckError."""
        exception = requests.ConnectionError("Connection failed")
        session = FakeSession(raise_exception=exception)
        client = HIBPClient(session=session)

        with pytest.raises(BreachCheckError, match="Unable to reach Have I Been Pwned"):
            client.count("password")

    def test_api_url_format(self):
        """Test that API URL is correctly formatted."""
        client = HIBPClient()

        assert client.API_URL == "https://api.pwnedpasswords.com/range/{}"

    def test_count_with_special_characters_password(self):
        """Test counting breach occurrences for password with special characters."""
        response_text = "ABCDEF:3\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(session=session)

        # Special characters password should still work
        count = client.count("p@ssw0rd!#$%&*")

        assert isinstance(count, int)

    def test_count_with_unicode_password(self):
        """Test counting breach occurrences for unicode password."""
        response_text = "ABCDEF:2\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(session=session)

        # Unicode password should be handled
        count = client.count("pässwörd🔐")

        assert isinstance(count, int)

    def test_count_with_very_long_password(self):
        """Test counting breach occurrences for very long password."""
        response_text = "ABCDEF:1\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(session=session)

        long_password = "x" * 10000
        count = client.count(long_password)

        assert isinstance(count, int)

    def test_count_exact_hash_match(self):
        """Test that exact suffix match is required."""
        # SHA1('password') = 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8
        # Suffix: 1E4C9B93F3F0682250B6CF8331B7EE68FD8
        response_text = "1E4C9B93F3F0682250B6CF8331B7EE68FD:10\n1E4C9B93F3F0682250B6CF8331B7EE68FD8:7\n1E4C9B93F3F0682250B6CF8331B7EE68FD80:5\n"
        session = FakeSession(response_text=response_text)
        client = HIBPClient(session=session)

        count = client.count("password")

        # Should only match exact suffix
        assert count == 7
