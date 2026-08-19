import secrets
import string
from dataclasses import dataclass


@dataclass(frozen=True)
class PasswordPolicy:
    """Constraint set used when generating a password.

    Attributes
    ----------
    letters : int, default=8
        Number of alphabetic characters to include.
    digits : int, default=4
        Number of numeric characters to include.
    symbols : int, default=2
        Number of symbol characters to include.
    symbols_charset : str, default='@#$%&!'
        Character set from which symbol values are chosen.
    """

    letters: int = 8
    digits: int = 4
    symbols: int = 2
    symbols_charset: str = "@#$%&!"


class PasswordGenerator:
    """Generate strong passwords and evaluate their estimated quality."""

    def generate(self, policy: PasswordPolicy) -> str:
        """Generate a randomized password matching the supplied policy.

        Parameters
        ----------
        policy : PasswordPolicy
            Composition rules for the generated password.

        Returns
        -------
        str
            Randomized password that matches the requested counts.

        Raises
        ------
        ValueError
            If any password component count is negative.
        """
        if min(policy.letters, policy.digits, policy.symbols) < 0:
            raise ValueError("Password counts cannot be negative")

        chars = (
            [secrets.choice(string.ascii_letters) for _ in range(policy.letters)]
            + [secrets.choice(string.digits) for _ in range(policy.digits)]
            + [secrets.choice(policy.symbols_charset) for _ in range(policy.symbols)]
        )

        if policy.letters >= 2:
            chars[0] = secrets.choice(string.ascii_uppercase)
            chars[1] = secrets.choice(string.ascii_lowercase)

        secrets.SystemRandom().shuffle(chars)
        return "".join(chars)

    @staticmethod
    def strength_message(password: str) -> str:
        """Return a textual strength assessment for a password.

        Parameters
        ----------
        password : str
            Password to evaluate.

        Returns
        -------
        str
            Guidance describing whether the password is weak, moderate, or strong.
        """
        if len(password) <= 8:
            return f"{password} too short. At least 8 characters to make it strong"

        symbols = set("!@#$%^&")
        lower = any(c.islower() for c in password)
        upper = any(c.isupper() for c in password)
        digit = any(c.isdigit() for c in password)
        symbol = any(c in symbols for c in password)

        if lower and upper and digit and symbol:
            return f"{password} is Great!"
        if lower and upper and digit:
            return f"{password} is Good, but could be great with additional symbols (!@#$%&)"
        if not lower or not upper:
            return "Better have a mix of capital and lowercase letters"
        if not digit:
            return "You can add numbers to make it stronger"
        return "Additional symbols (!@#$%&) should be added to make it stronger"
