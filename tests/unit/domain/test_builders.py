"""
Unit tests for TransactionBuilder domain component.

This module provides comprehensive unit tests for the TransactionBuilder class,
following the testing strategy with proper mock dependencies and behavior-focused testing.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from domain.builders import TransactionBuilder
from domain.models import Currency, PaymentMethod, Transaction


class TestTransactionBuilder:
    """Unit tests for TransactionBuilder class"""

    @pytest.fixture
    def mock_date_converter(self):
        """Create mock date converter"""
        converter = Mock()
        converter.convert_dd_mm_yy.return_value = date(2025, 6, 5)
        return converter

    @pytest.fixture
    def mock_amount_parser(self):
        """Create mock amount parser"""
        parser = Mock()
        parser.parse_european_format.return_value = Decimal("1234.56")
        return parser

    @pytest.fixture
    def transaction_builder(self, mock_date_converter, mock_amount_parser):
        """Create TransactionBuilder instance with mocked dependencies"""
        return TransactionBuilder(mock_date_converter, mock_amount_parser)

    def test_initialization_with_dependencies(
        self, mock_date_converter, mock_amount_parser
    ):
        """Test that TransactionBuilder initializes correctly with dependencies"""
        # Act
        builder = TransactionBuilder(mock_date_converter, mock_amount_parser)

        # Assert
        assert builder._date_converter is mock_date_converter
        assert builder._amount_parser is mock_amount_parser

    def test_build_from_pdf_line_success(
        self, transaction_builder, mock_date_converter, mock_amount_parser
    ):
        """Test successful transaction building from PDF line components"""
        # Arrange
        date_str = "05.06.25"
        description = "TEST TRANSACTION"
        amount_str = "1.234,56"
        currency = Currency.ARS
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transaction = transaction_builder.build_from_pdf_line(
            date_str=date_str,
            description=description,
            amount_str=amount_str,
            currency=currency,
            payment_method=payment_method,
        )

        # Assert
        assert isinstance(transaction, Transaction)
        assert transaction.date == date(2025, 6, 5)
        assert transaction.description == "TEST TRANSACTION"
        assert transaction.amount == Decimal("1234.56")
        assert transaction.currency == Currency.ARS
        assert transaction.payment_method == PaymentMethod.BBVA_VISA

        # Verify dependencies were called correctly
        mock_date_converter.convert_dd_mm_yy.assert_called_once_with("05.06.25")
        mock_amount_parser.parse_european_format.assert_called_once_with("1.234,56")

    def test_build_from_pdf_line_with_usd_currency(
        self, transaction_builder, mock_date_converter, mock_amount_parser
    ):
        """Test transaction building with USD currency"""
        # Arrange
        mock_amount_parser.parse_european_format.return_value = Decimal("100.00")

        # Act
        transaction = transaction_builder.build_from_pdf_line(
            date_str="10.05.25",
            description="USD TRANSACTION",
            amount_str="100,00",
            currency=Currency.USD,
            payment_method=PaymentMethod.MACRO_VISA,
        )

        # Assert
        assert transaction.currency == Currency.USD
        assert transaction.payment_method == PaymentMethod.MACRO_VISA
        assert transaction.amount == Decimal("100.00")

    def test_build_from_pdf_line_strips_whitespace(
        self, transaction_builder, mock_date_converter, mock_amount_parser
    ):
        """Test that whitespace is properly stripped from input components"""
        # Act
        transaction_builder.build_from_pdf_line(
            date_str="  05.06.25  ",
            description="  TEST TRANSACTION  ",
            amount_str="  1.234,56  ",
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        # Assert
        mock_date_converter.convert_dd_mm_yy.assert_called_once_with("05.06.25")
        mock_amount_parser.parse_european_format.assert_called_once_with("1.234,56")

    def test_build_from_pdf_line_empty_date_string(self, transaction_builder):
        """Test that empty date string raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Date string cannot be empty"):
            transaction_builder.build_from_pdf_line(
                date_str="",
                description="TEST",
                amount_str="100,00",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_whitespace_only_date_string(self, transaction_builder):
        """Test that whitespace-only date string raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Date string cannot be empty"):
            transaction_builder.build_from_pdf_line(
                date_str="   ",
                description="TEST",
                amount_str="100,00",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_empty_description(self, transaction_builder):
        """Test that empty description raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Description cannot be empty"):
            transaction_builder.build_from_pdf_line(
                date_str="05.06.25",
                description="",
                amount_str="100,00",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_whitespace_only_description(self, transaction_builder):
        """Test that whitespace-only description raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Description cannot be empty"):
            transaction_builder.build_from_pdf_line(
                date_str="05.06.25",
                description="   ",
                amount_str="100,00",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_empty_amount_string(self, transaction_builder):
        """Test that empty amount string raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Amount string cannot be empty"):
            transaction_builder.build_from_pdf_line(
                date_str="05.06.25",
                description="TEST",
                amount_str="",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_whitespace_only_amount_string(
        self, transaction_builder
    ):
        """Test that whitespace-only amount string raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Amount string cannot be empty"):
            transaction_builder.build_from_pdf_line(
                date_str="05.06.25",
                description="TEST",
                amount_str="   ",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_date_converter_error(
        self, transaction_builder, mock_date_converter, mock_amount_parser
    ):
        """Test handling of date converter errors"""
        # Arrange
        mock_date_converter.convert_dd_mm_yy.side_effect = ValueError(
            "Invalid date format"
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Failed to build transaction from PDF line components"
        ):
            transaction_builder.build_from_pdf_line(
                date_str="invalid",
                description="TEST",
                amount_str="100,00",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_amount_parser_error(
        self, transaction_builder, mock_date_converter, mock_amount_parser
    ):
        """Test handling of amount parser errors"""
        # Arrange
        mock_amount_parser.parse_european_format.side_effect = ValueError(
            "Invalid amount format"
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Failed to build transaction from PDF line components"
        ):
            transaction_builder.build_from_pdf_line(
                date_str="05.06.25",
                description="TEST",
                amount_str="invalid",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_unexpected_error(
        self, transaction_builder, mock_date_converter, mock_amount_parser
    ):
        """Test handling of unexpected errors"""
        # Arrange
        mock_date_converter.convert_dd_mm_yy.side_effect = RuntimeError(
            "Unexpected error"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Unexpected error building transaction"):
            transaction_builder.build_from_pdf_line(
                date_str="05.06.25",
                description="TEST",
                amount_str="100,00",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_with_negative_amount(
        self, transaction_builder, mock_date_converter, mock_amount_parser
    ):
        """Test transaction building with negative amount"""
        # Arrange
        mock_amount_parser.parse_european_format.return_value = Decimal("-1234.56")

        # Act
        transaction = transaction_builder.build_from_pdf_line(
            date_str="05.06.25",
            description="SU PAGO EN PESOS",
            amount_str="-1.234,56",
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        # Assert
        assert transaction.amount == Decimal("-1234.56")
        assert transaction.description == "SU PAGO EN PESOS"

    def test_build_from_pdf_line_with_different_payment_methods(
        self, transaction_builder, mock_date_converter, mock_amount_parser
    ):
        """Test transaction building with different payment methods"""
        # Test BBVA Mastercard
        transaction1 = transaction_builder.build_from_pdf_line(
            date_str="05.06.25",
            description="MASTERCARD TRANSACTION",
            amount_str="100,00",
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_MASTERCARD,
        )
        assert transaction1.payment_method == PaymentMethod.BBVA_MASTERCARD

        # Test Macro Account
        transaction2 = transaction_builder.build_from_pdf_line(
            date_str="05.06.25",
            description="ACCOUNT TRANSACTION",
            amount_str="200,00",
            currency=Currency.ARS,
            payment_method=PaymentMethod.MACRO_ACCOUNT,
        )
        assert transaction2.payment_method == PaymentMethod.MACRO_ACCOUNT

    def test_build_from_pdf_line_preserves_description_content(
        self, transaction_builder, mock_date_converter, mock_amount_parser
    ):
        """Test that description content is preserved exactly"""
        # Arrange
        complex_description = "020396* PERSONAL FLOW 300060254971003"

        # Act
        transaction = transaction_builder.build_from_pdf_line(
            date_str="05.06.25",
            description=complex_description,
            amount_str="1.234,56",
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        # Assert
        assert transaction.description == complex_description
