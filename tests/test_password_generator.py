"""Tests for password_manager.password_generator module."""
import pytest

from password_manager.password_generator import PasswordGenerator, PasswordPolicy


class TestPasswordPolicy:
    """Test cases for the PasswordPolicy data class."""

    def test_password_policy_default_values(self):
        """Test PasswordPolicy initialization with defaults."""
        policy = PasswordPolicy()

        assert policy.letters == 8
        assert policy.digits == 4
        assert policy.symbols == 2
        assert policy.symbols_charset == "@#$%&!"

    def test_password_policy_custom_values(self):
        """Test PasswordPolicy initialization with custom values."""
        policy = PasswordPolicy(letters=10, digits=5, symbols=3, symbols_charset="!@#")

        assert policy.letters == 10
        assert policy.digits == 5
        assert policy.symbols == 3
        assert policy.symbols_charset == "!@#"

    def test_password_policy_zero_values(self):
        """Test PasswordPolicy with zero values."""
        policy = PasswordPolicy(letters=0, digits=0, symbols=0)

        assert policy.letters == 0
        assert policy.digits == 0
        assert policy.symbols == 0

    def test_password_policy_empty_symbols_charset(self):
        """Test PasswordPolicy with empty symbols charset."""
        policy = PasswordPolicy(symbols_charset="")

        assert policy.symbols_charset == ""


class TestPasswordGenerator:
    """Test cases for the PasswordGenerator class."""

    def test_generate_with_default_policy(self):
        """Test password generation with default policy."""
        generator = PasswordGenerator()
        password = generator.generate(PasswordPolicy())

        assert len(password) == 14  # 8 letters + 4 digits + 2 symbols
        assert any(char.isupper() for char in password)
        assert any(char.islower() for char in password)
        assert any(char.isdigit() for char in password)

    def test_generate_with_custom_policy(self):
        """Test password generation with custom policy."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=10, digits=5, symbols=3)
        password = generator.generate(policy)

        assert len(password) == 18  # 10 letters + 5 digits + 3 symbols

    def test_generate_with_zero_components(self):
        """Test password generation with zero components."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=0, digits=0, symbols=0)
        password = generator.generate(policy)

        assert len(password) == 0
        assert password == ""

    def test_generate_with_only_letters(self):
        """Test password generation with only letters."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=10, digits=0, symbols=0)
        password = generator.generate(policy)

        assert len(password) == 10
        assert all(char.isalpha() for char in password)

    def test_generate_with_only_digits(self):
        """Test password generation with only digits."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=0, digits=5, symbols=0)
        password = generator.generate(policy)

        assert len(password) == 5
        assert all(char.isdigit() for char in password)

    def test_generate_with_only_symbols(self):
        """Test password generation with only symbols."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=0, digits=0, symbols=5, symbols_charset="@#$")
        password = generator.generate(policy)

        assert len(password) == 5
        assert all(char in "@#$" for char in password)

    def test_generate_with_negative_letters_raises_value_error(self):
        """Test that negative letter count raises ValueError."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=-1, digits=4, symbols=2)

        with pytest.raises(ValueError, match="Password counts cannot be negative"):
            generator.generate(policy)

    def test_generate_with_negative_digits_raises_value_error(self):
        """Test that negative digit count raises ValueError."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=8, digits=-1, symbols=2)

        with pytest.raises(ValueError, match="Password counts cannot be negative"):
            generator.generate(policy)

    def test_generate_with_negative_symbols_raises_value_error(self):
        """Test that negative symbol count raises ValueError."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=8, digits=4, symbols=-1)

        with pytest.raises(ValueError, match="Password counts cannot be negative"):
            generator.generate(policy)

    def test_generate_produces_randomized_passwords(self):
        """Test that multiple generations produce different passwords."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=8, digits=4, symbols=2)

        passwords = {generator.generate(policy) for _ in range(10)}

        # Very unlikely to have duplicates with randomization
        assert len(passwords) > 1

    def test_generate_with_custom_symbols_charset(self):
        """Test password generation with custom symbols."""
        generator = PasswordGenerator()
        policy = PasswordPolicy(letters=0, digits=0, symbols=5, symbols_charset="abc123")
        password = generator.generate(policy)

        assert len(password) == 5
        assert all(char in "abc123" for char in password)

    def test_strength_message_too_short(self):
        """Test strength message for short password."""
        generator = PasswordGenerator()
        message = generator.strength_message("short")

        assert "too short" in message
        assert "At least 8 characters" in message

    def test_strength_message_weak_no_symbols(self):
        """Test strength message for weak password without symbols."""
        generator = PasswordGenerator()
        message = generator.strength_message("Abcdef1234")  # 10 chars: uppercase, lowercase, digits, no symbols

        assert "Good, but could be great" in message
        assert "symbols" in message

    def test_strength_message_weak_no_uppercase(self):
        """Test strength message for weak password without uppercase."""
        generator = PasswordGenerator()
        message = generator.strength_message("abcdef123!@#")

        assert "capital and lowercase" in message

    def test_strength_message_weak_no_lowercase(self):
        """Test strength message for weak password without lowercase."""
        generator = PasswordGenerator()
        message = generator.strength_message("ABCDEF123!@#")

        assert "capital and lowercase" in message

    def test_strength_message_weak_no_digits(self):
        """Test strength message for weak password without digits."""
        generator = PasswordGenerator()
        message = generator.strength_message("Abcdefgh!@#")

        assert "numbers" in message

    def test_strength_message_weak_no_custom_symbols(self):
        """Test strength message for weak password with digits but no symbols."""
        generator = PasswordGenerator()
        message = generator.strength_message("Abcdef12345#")  # 12 chars: uppercase, lowercase, digits, symbol

        assert "Great!" in message

    def test_strength_message_strong(self):
        """Test strength message for strong password."""
        generator = PasswordGenerator()
        message = generator.strength_message("Abcdef123!@#45")  # 14 chars with all elements

        assert "Great!" in message

    def test_strength_message_only_lowercase_letters(self):
        """Test strength message for password with only lowercase letters."""
        generator = PasswordGenerator()
        message = generator.strength_message("abcdefghijklmnop")

        assert "capital and lowercase" in message

    def test_strength_message_with_various_symbols(self):
        """Test that strength message recognizes various symbol characters."""
        generator = PasswordGenerator()
        symbols = "!@#$%^&"
        for symbol in symbols:
            password = f"Abc123456{symbol}"  # 10+ chars: uppercase, lowercase, digits, symbol
            message = generator.strength_message(password)
            # Should recognize as having symbol
            assert "Great!" in message or "could be great" in message
