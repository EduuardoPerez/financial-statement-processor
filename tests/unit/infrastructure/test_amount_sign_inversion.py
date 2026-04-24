"""Tests for AmountSignInversionConfig functionality."""

import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from src.domain.models import Currency, PaymentMethod, Transaction
from src.infrastructure.config import AmountSignInversionConfig, ApplicationConfig
from src.infrastructure.repositories import ExcelStatementRepository


class TestAmountSignInversionConfig:
    """Test AmountSignInversionConfig dataclass functionality."""

    def test_creation_with_defaults(self):
        """Test creating config with all default values."""
        config = AmountSignInversionConfig()

        assert config.invert_all is False
        assert config.invert_patterns == []
        assert config.exclude_patterns == []

    def test_creation_with_custom_values(self):
        """Test creating config with custom values."""
        config = AmountSignInversionConfig(
            invert_all=True,
            invert_patterns=["*_VISA", "*_MASTERCARD"],
            exclude_patterns=["*_ACCOUNT"],
        )

        assert config.invert_all is True
        assert config.invert_patterns == ["*_VISA", "*_MASTERCARD"]
        assert config.exclude_patterns == ["*_ACCOUNT"]

    def test_should_invert_with_invert_all_true(self):
        """Test that invert_all=True inverts all payment methods."""
        config = AmountSignInversionConfig(invert_all=True)

        assert config.should_invert(PaymentMethod.MACRO_VISA) is True
        assert config.should_invert(PaymentMethod.BBVA_ACCOUNT) is True
        assert config.should_invert(PaymentMethod.MERCADOPAGO) is True

    def test_should_invert_with_invert_all_false(self):
        """Test that invert_all=False does not invert any payment method."""
        config = AmountSignInversionConfig(invert_all=False)

        assert config.should_invert(PaymentMethod.MACRO_VISA) is False
        assert config.should_invert(PaymentMethod.BBVA_ACCOUNT) is False
        assert config.should_invert(PaymentMethod.MERCADOPAGO) is False

    def test_should_invert_with_pattern_matching(self):
        """Test pattern matching with fnmatch wildcards."""
        config = AmountSignInversionConfig(
            invert_all=False,
            invert_patterns=["*_VISA", "*_MASTERCARD"],
        )

        # Should match *_VISA pattern
        assert config.should_invert(PaymentMethod.MACRO_VISA) is True
        assert config.should_invert(PaymentMethod.BBVA_VISA) is True

        # Should match *_MASTERCARD pattern
        assert config.should_invert(PaymentMethod.BBVA_MASTERCARD) is True

        # Should not match any pattern
        assert config.should_invert(PaymentMethod.BBVA_ACCOUNT) is False
        assert config.should_invert(PaymentMethod.MERCADOPAGO) is False

    def test_should_invert_with_bank_prefix_pattern(self):
        """Test pattern matching with bank prefix wildcards."""
        config = AmountSignInversionConfig(
            invert_all=False,
            invert_patterns=["BBVA_*"],
        )

        assert config.should_invert(PaymentMethod.BBVA_VISA) is True
        assert config.should_invert(PaymentMethod.BBVA_MASTERCARD) is True
        assert config.should_invert(PaymentMethod.BBVA_ACCOUNT) is True

        assert config.should_invert(PaymentMethod.MACRO_VISA) is False
        assert config.should_invert(PaymentMethod.MACRO_ACCOUNT) is False
        assert config.should_invert(PaymentMethod.MERCADOPAGO) is False

    def test_exclude_patterns_have_highest_priority(self):
        """Test that exclude_patterns override both invert_all and invert_patterns."""
        config = AmountSignInversionConfig(
            invert_all=True,
            invert_patterns=["*_VISA"],
            exclude_patterns=["*_ACCOUNT", "MERCADOPAGO"],
        )

        # Should be excluded despite invert_all=True
        assert config.should_invert(PaymentMethod.BBVA_ACCOUNT) is False
        assert config.should_invert(PaymentMethod.MACRO_ACCOUNT) is False
        assert config.should_invert(PaymentMethod.MERCADOPAGO) is False

        # Should be inverted due to invert_all=True
        assert config.should_invert(PaymentMethod.BBVA_VISA) is True
        assert config.should_invert(PaymentMethod.BBVA_MASTERCARD) is True

    def test_invert_patterns_override_invert_all(self):
        """Test that invert_patterns work when invert_all is False."""
        config = AmountSignInversionConfig(
            invert_all=False,
            invert_patterns=["*_VISA"],
        )

        # Only VISA cards should be inverted
        assert config.should_invert(PaymentMethod.MACRO_VISA) is True
        assert config.should_invert(PaymentMethod.BBVA_VISA) is True

        # Others should not be inverted
        assert config.should_invert(PaymentMethod.BBVA_MASTERCARD) is False
        assert config.should_invert(PaymentMethod.BBVA_ACCOUNT) is False

    def test_exact_match_pattern(self):
        """Test exact match patterns without wildcards."""
        config = AmountSignInversionConfig(
            invert_all=False,
            invert_patterns=["MACRO_VISA"],
        )

        assert config.should_invert(PaymentMethod.MACRO_VISA) is True
        assert config.should_invert(PaymentMethod.BBVA_VISA) is False


class TestApplicationConfigAmountSignInversion:
    """Test ApplicationConfig loading of amount_sign_inversion section."""

    def test_from_yaml_without_amount_sign_inversion(self):
        """Test loading YAML without amount_sign_inversion section."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = ApplicationConfig.from_yaml(Path("test.yaml"))

            assert config.amount_sign_inversion.invert_all is False
            assert config.amount_sign_inversion.invert_patterns == []
            assert config.amount_sign_inversion.exclude_patterns == []

    def test_from_yaml_with_amount_sign_inversion(self):
        """Test loading YAML with amount_sign_inversion section."""
        yaml_content = """
input_directory: "input"
output_directory: "output"

amount_sign_inversion:
  invert_all: true
  invert_patterns:
    - "*_VISA"
    - "*_MASTERCARD"
  exclude_patterns:
    - "*_ACCOUNT"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = ApplicationConfig.from_yaml(Path("test.yaml"))

            assert config.amount_sign_inversion.invert_all is True
            assert config.amount_sign_inversion.invert_patterns == [
                "*_VISA",
                "*_MASTERCARD",
            ]
            assert config.amount_sign_inversion.exclude_patterns == ["*_ACCOUNT"]

    def test_from_yaml_with_empty_amount_sign_inversion(self):
        """Test loading YAML with empty amount_sign_inversion section."""
        yaml_content = """
input_directory: "input"
output_directory: "output"

amount_sign_inversion:
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = ApplicationConfig.from_yaml(Path("test.yaml"))

            assert config.amount_sign_inversion.invert_all is False
            assert config.amount_sign_inversion.invert_patterns == []
            assert config.amount_sign_inversion.exclude_patterns == []

    def test_from_yaml_with_partial_amount_sign_inversion(self):
        """Test loading YAML with partial amount_sign_inversion section."""
        yaml_content = """
input_directory: "input"
output_directory: "output"

amount_sign_inversion:
  invert_patterns:
    - "*_VISA"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = ApplicationConfig.from_yaml(Path("test.yaml"))

            assert config.amount_sign_inversion.invert_all is False
            assert config.amount_sign_inversion.invert_patterns == ["*_VISA"]
            assert config.amount_sign_inversion.exclude_patterns == []


class TestApplicationConfigEnvironmentAmountSignInversion:
    """Test ApplicationConfig loading from environment variables."""

    def test_from_environment_without_inversion_vars(self):
        """Test loading from environment without inversion variables."""
        with patch.dict(os.environ, {}, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.amount_sign_inversion.invert_all is False
            assert config.amount_sign_inversion.invert_patterns == []
            assert config.amount_sign_inversion.exclude_patterns == []

    def test_from_environment_with_invert_all(self):
        """Test loading FSP_AMOUNT_INVERT_ALL from environment."""
        env_vars = {"FSP_AMOUNT_INVERT_ALL": "true"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.amount_sign_inversion.invert_all is True

    def test_from_environment_with_invert_patterns(self):
        """Test loading FSP_AMOUNT_INVERT_PATTERNS from environment."""
        env_vars = {"FSP_AMOUNT_INVERT_PATTERNS": "*_VISA,*_MASTERCARD"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.amount_sign_inversion.invert_patterns == [
                "*_VISA",
                "*_MASTERCARD",
            ]

    def test_from_environment_with_exclude_patterns(self):
        """Test loading FSP_AMOUNT_EXCLUDE_PATTERNS from environment."""
        env_vars = {"FSP_AMOUNT_EXCLUDE_PATTERNS": "*_ACCOUNT,MERCADOPAGO"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.amount_sign_inversion.exclude_patterns == [
                "*_ACCOUNT",
                "MERCADOPAGO",
            ]

    def test_from_environment_with_all_inversion_vars(self):
        """Test loading all amount sign inversion variables from environment."""
        env_vars = {
            "FSP_AMOUNT_INVERT_ALL": "false",
            "FSP_AMOUNT_INVERT_PATTERNS": "*_VISA,*_MASTERCARD",
            "FSP_AMOUNT_EXCLUDE_PATTERNS": "*_ACCOUNT",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.amount_sign_inversion.invert_all is False
            assert config.amount_sign_inversion.invert_patterns == [
                "*_VISA",
                "*_MASTERCARD",
            ]
            assert config.amount_sign_inversion.exclude_patterns == ["*_ACCOUNT"]

    def test_parse_env_list_empty_string(self):
        """Test _parse_env_list with empty string."""
        result = ApplicationConfig._parse_env_list("")
        assert result == []

    def test_parse_env_list_whitespace_only(self):
        """Test _parse_env_list with whitespace only."""
        result = ApplicationConfig._parse_env_list("   ")
        assert result == []

    def test_parse_env_list_single_item(self):
        """Test _parse_env_list with single item."""
        result = ApplicationConfig._parse_env_list("*_VISA")
        assert result == ["*_VISA"]

    def test_parse_env_list_multiple_items(self):
        """Test _parse_env_list with multiple items."""
        result = ApplicationConfig._parse_env_list("*_VISA,*_MASTERCARD,MERCADOPAGO")
        assert result == ["*_VISA", "*_MASTERCARD", "MERCADOPAGO"]

    def test_parse_env_list_with_spaces(self):
        """Test _parse_env_list strips whitespace from items."""
        result = ApplicationConfig._parse_env_list(
            "*_VISA , *_MASTERCARD , MERCADOPAGO"
        )
        assert result == ["*_VISA", "*_MASTERCARD", "MERCADOPAGO"]

    def test_parse_env_list_filters_empty_items(self):
        """Test _parse_env_list filters out empty items."""
        result = ApplicationConfig._parse_env_list("*_VISA,,*_MASTERCARD,")
        assert result == ["*_VISA", "*_MASTERCARD"]


class TestRepositoryAmountSignInversion:
    """Test ExcelStatementRepository applies amount sign inversion correctly."""

    def _create_transaction(
        self, amount: Decimal, payment_method: PaymentMethod
    ) -> Transaction:
        """Helper to create a test transaction."""
        return Transaction(
            date=date(2024, 1, 15),
            description="Test transaction",
            amount=amount,
            currency=Currency.ARS,
            payment_method=payment_method,
        )

    def _create_output_config_dot_separator(self):
        """Create output config with dot decimal separator for easier test assertions."""
        from src.infrastructure.config import OutputConfig

        return OutputConfig(decimal_separator=".")

    def test_repository_inverts_amount_when_configured(self):
        """Test that repository inverts amount when should_invert returns True."""
        inversion_config = AmountSignInversionConfig(
            invert_all=False,
            invert_patterns=["*_VISA"],
        )

        file_reader = MagicMock()
        file_writer = MagicMock()

        repository = ExcelStatementRepository(
            file_reader=file_reader,
            file_writer=file_writer,
            output_config=self._create_output_config_dot_separator(),
            amount_sign_inversion=inversion_config,
        )

        # Create a mock statement with a VISA transaction
        from src.domain.models import Statement

        transaction = self._create_transaction(
            Decimal("100.50"), PaymentMethod.MACRO_VISA
        )
        statement = Statement(
            payment_method=PaymentMethod.MACRO_VISA, transactions=[transaction]
        )

        df = repository._transactions_to_dataframe(statement.transactions)

        # Amount should be inverted (negative)
        assert df["Amount"].iloc[0] == "-100.5"

    def test_repository_does_not_invert_when_not_configured(self):
        """Test that repository does not invert amount when should_invert returns False."""
        inversion_config = AmountSignInversionConfig(
            invert_all=False,
            invert_patterns=["*_VISA"],
        )

        file_reader = MagicMock()
        file_writer = MagicMock()

        repository = ExcelStatementRepository(
            file_reader=file_reader,
            file_writer=file_writer,
            output_config=self._create_output_config_dot_separator(),
            amount_sign_inversion=inversion_config,
        )

        # Create a mock statement with an ACCOUNT transaction (not matched)
        from src.domain.models import Statement

        transaction = self._create_transaction(
            Decimal("100.50"), PaymentMethod.BBVA_ACCOUNT
        )
        statement = Statement(
            payment_method=PaymentMethod.BBVA_ACCOUNT, transactions=[transaction]
        )

        df = repository._transactions_to_dataframe(statement.transactions)

        # Amount should not be inverted (positive)
        assert df["Amount"].iloc[0] == "100.5"

    def test_repository_inverts_negative_amounts(self):
        """Test that inverting a negative amount makes it positive."""
        inversion_config = AmountSignInversionConfig(
            invert_all=False,
            invert_patterns=["*_VISA"],
        )

        file_reader = MagicMock()
        file_writer = MagicMock()

        repository = ExcelStatementRepository(
            file_reader=file_reader,
            file_writer=file_writer,
            output_config=self._create_output_config_dot_separator(),
            amount_sign_inversion=inversion_config,
        )

        from src.domain.models import Statement

        transaction = self._create_transaction(
            Decimal("-50.25"), PaymentMethod.MACRO_VISA
        )
        statement = Statement(
            payment_method=PaymentMethod.MACRO_VISA, transactions=[transaction]
        )

        df = repository._transactions_to_dataframe(statement.transactions)

        # Negative amount should become positive when inverted
        assert df["Amount"].iloc[0] == "50.25"

    def test_repository_consolidated_inverts_amount_when_configured(self):
        """Test that consolidated statement also applies inversion."""
        inversion_config = AmountSignInversionConfig(
            invert_all=False,
            invert_patterns=["*_VISA"],
        )

        file_reader = MagicMock()
        file_writer = MagicMock()

        repository = ExcelStatementRepository(
            file_reader=file_reader,
            file_writer=file_writer,
            output_config=self._create_output_config_dot_separator(),
            amount_sign_inversion=inversion_config,
        )

        from src.domain.models import ConsolidatedStatement

        transaction_visa = self._create_transaction(
            Decimal("100.00"), PaymentMethod.MACRO_VISA
        )
        transaction_account = self._create_transaction(
            Decimal("200.00"), PaymentMethod.BBVA_ACCOUNT
        )

        consolidated = ConsolidatedStatement(
            transactions=[transaction_visa, transaction_account],
            source_statements=[],
            duplicate_count=0,
        )

        df = repository._transactions_to_dataframe(consolidated.transactions)

        # VISA should be inverted, ACCOUNT should not
        assert df["Amount"].iloc[0] == "-100.0"
        assert df["Amount"].iloc[1] == "200.0"

    def test_repository_default_no_inversion(self):
        """Test that repository does not invert by default."""
        file_reader = MagicMock()
        file_writer = MagicMock()

        # No amount_sign_inversion config passed (uses default)
        repository = ExcelStatementRepository(
            file_reader=file_reader,
            file_writer=file_writer,
            output_config=self._create_output_config_dot_separator(),
        )

        from src.domain.models import Statement

        transaction = self._create_transaction(
            Decimal("100.50"), PaymentMethod.MACRO_VISA
        )
        statement = Statement(
            payment_method=PaymentMethod.MACRO_VISA, transactions=[transaction]
        )

        df = repository._transactions_to_dataframe(statement.transactions)

        # Amount should not be inverted by default
        assert df["Amount"].iloc[0] == "100.5"
