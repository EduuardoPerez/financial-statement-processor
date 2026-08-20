"""
Tests for ExcelStatementRepository decimal separator functionality.

This module tests the repository's ability to format amounts with configured
decimal separators in Excel output.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from domain.models import Currency, PaymentMethod, Statement, Transaction
from infrastructure.config import OutputConfig, PaymentMethodMappingConfig
from infrastructure.repositories import ExcelStatementRepository


class TestExcelRepositoryDecimalSeparator:
    """Test decimal separator formatting in ExcelStatementRepository."""

    @pytest.fixture
    def mock_file_reader(self):
        """Create mock file reader."""
        mock = Mock()
        mock.exists.return_value = True
        mock.read.return_value = b"test data"
        return mock

    @pytest.fixture
    def mock_file_writer(self):
        """Create mock file writer."""
        mock = Mock()
        return mock

    @pytest.fixture
    def sample_statement(self):
        """Create sample statement for testing."""
        transactions = [
            Transaction(
                date=date(2025, 1, 15),
                description="Test Transaction 1",
                amount=Decimal("1234.56"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 1, 16),
                description="Test Transaction 2",
                amount=Decimal("987.43"),
                currency=Currency.USD,
                payment_method=PaymentMethod.MACRO_VISA,
            ),
        ]
        return Statement(
            payment_method=PaymentMethod.BBVA_VISA, transactions=transactions
        )

    def test_statement_to_dataframe_default_comma_separator(
        self, mock_file_reader, mock_file_writer, sample_statement
    ):
        """Test DataFrame creation with default comma decimal separator."""
        output_config = OutputConfig(decimal_separator=",")
        repository = ExcelStatementRepository(
            mock_file_reader,
            mock_file_writer,
            PaymentMethodMappingConfig(),
            output_config,
        )

        df = repository._transactions_to_dataframe(sample_statement.transactions)

        # Check that amounts are formatted with comma separator
        assert df.iloc[0]["Amount"] == "1234,56"
        assert df.iloc[1]["Amount"] == "987,43"

    def test_statement_to_dataframe_dot_separator(
        self, mock_file_reader, mock_file_writer, sample_statement
    ):
        """Test DataFrame creation with dot decimal separator."""
        output_config = OutputConfig(decimal_separator=".")
        repository = ExcelStatementRepository(
            mock_file_reader,
            mock_file_writer,
            PaymentMethodMappingConfig(),
            output_config,
        )

        df = repository._transactions_to_dataframe(sample_statement.transactions)

        # Check that amounts are formatted with dot separator
        assert df.iloc[0]["Amount"] == "1234.56"
        assert df.iloc[1]["Amount"] == "987.43"

    def test_statement_to_dataframe_semicolon_separator(
        self, mock_file_reader, mock_file_writer, sample_statement
    ):
        """Test DataFrame creation with semicolon decimal separator."""
        output_config = OutputConfig(decimal_separator=";")
        repository = ExcelStatementRepository(
            mock_file_reader,
            mock_file_writer,
            PaymentMethodMappingConfig(),
            output_config,
        )

        df = repository._transactions_to_dataframe(sample_statement.transactions)

        # Check that amounts are formatted with semicolon separator
        assert df.iloc[0]["Amount"] == "1234;56"
        assert df.iloc[1]["Amount"] == "987;43"

    def test_consolidated_to_dataframe_decimal_separator(
        self, mock_file_reader, mock_file_writer
    ):
        """Test consolidated DataFrame creation with decimal separator."""
        from domain.models import ConsolidatedStatement

        transactions = [
            Transaction(
                date=date(2025, 1, 15),
                description="Consolidated Transaction",
                amount=Decimal("5678.90"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )
        ]
        consolidated = ConsolidatedStatement(transactions=transactions)

        output_config = OutputConfig(decimal_separator=".")
        repository = ExcelStatementRepository(
            mock_file_reader,
            mock_file_writer,
            PaymentMethodMappingConfig(),
            output_config,
        )

        df = repository._transactions_to_dataframe(consolidated.transactions)

        # Check that amount is formatted with dot separator
        assert df.iloc[0]["Amount"] == "5678.9"

    def test_repository_initialization_with_defaults(
        self, mock_file_reader, mock_file_writer
    ):
        """Test repository initialization with default configurations."""
        repository = ExcelStatementRepository(mock_file_reader, mock_file_writer)

        # Check that defaults are applied
        assert repository._output_config.decimal_separator == ","
        assert repository._payment_method_mapping is not None

    def test_negative_amounts_with_decimal_separator(
        self, mock_file_reader, mock_file_writer
    ):
        """Test formatting of negative amounts with decimal separator."""
        transactions = [
            Transaction(
                date=date(2025, 1, 15),
                description="Negative Transaction",
                amount=Decimal("-1500.75"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )
        ]
        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA, transactions=transactions
        )

        output_config = OutputConfig(decimal_separator=",")
        repository = ExcelStatementRepository(
            mock_file_reader,
            mock_file_writer,
            PaymentMethodMappingConfig(),
            output_config,
        )

        df = repository._transactions_to_dataframe(statement.transactions)

        # Check that negative amount is formatted correctly
        assert df.iloc[0]["Amount"] == "-1500,75"
