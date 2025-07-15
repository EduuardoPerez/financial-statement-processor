"""
Unit tests for XLSXStatementParser - BBVA Mastercard XLSX support.

This module provides unit tests for XLSX parsing functionality, specifically
testing the dual-format support for Mercadopago and BBVA Mastercard XLSX files.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from domain.builders import TransactionBuilder
from domain.models import Currency, PaymentMethod, Statement, Transaction
from infrastructure.parsers.xlsx_parser import XLSXStatementParser


class TestXLSXStatementParser:
    """Unit tests for XLSXStatementParser with dual-format support"""

    @pytest.fixture
    def mock_detector(self):
        """Create mock payment method detector"""
        detector = Mock()
        detector.detect_from_filename.return_value = PaymentMethod.BBVA_MASTERCARD
        return detector

    @pytest.fixture
    def mock_transaction_builder(self):
        """Create mock transaction builder"""
        builder = Mock(spec=TransactionBuilder)

        # Create sample BBVA Mastercard transaction
        sample_transaction = Transaction(
            date=date(2025, 7, 7),
            description="Onlyfans.Com",
            amount=Decimal("35.00"),
            currency=Currency.USD,
            payment_method=PaymentMethod.BBVA_MASTERCARD,
        )
        builder.build_from_xls_data.return_value = sample_transaction
        return builder

    @pytest.fixture
    def xlsx_parser(self, mock_detector, mock_transaction_builder):
        """Create XLSXStatementParser instance with mocked dependencies"""
        return XLSXStatementParser(mock_detector, mock_transaction_builder)

    def test_can_parse_xlsx_files(self, xlsx_parser):
        """Test that parser can detect XLSX files"""
        # Arrange & Act & Assert
        assert xlsx_parser.can_parse(Path("statement.xlsx")) is True
        assert xlsx_parser.can_parse(Path("statement.XLSX")) is True
        assert xlsx_parser.can_parse(Path("statement.pdf")) is False
        assert xlsx_parser.can_parse(Path("statement.xls")) is False
        assert xlsx_parser.can_parse(Path("statement.csv")) is False

    def test_get_supported_extensions(self, xlsx_parser):
        """Test that parser returns correct supported extensions"""
        # Arrange & Act
        extensions = xlsx_parser.get_supported_extensions()

        # Assert
        assert extensions == {".xlsx"}

    @patch("pandas.read_excel")
    def test_load_xlsx_data_bbva_mastercard(self, mock_read_excel, xlsx_parser):
        """Test loading BBVA Mastercard XLSX data with special header handling"""
        # Arrange
        test_file = Path("BBVA-Mastercard-test.xlsx")
        mock_df = pd.DataFrame(
            {
                "Fecha y hora": ["07/07/25", "15/03/25"],
                "Movimientos": ["Onlyfans.Com", "ON FIT"],
                "Cuota": ["-", "05/06"],
                "Monto": ["USD 35,00", "$ 107.970,00"],
            }
        )
        mock_read_excel.return_value = mock_df

        # Act
        result_df = xlsx_parser._load_xlsx_data(test_file)

        # Assert
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 2
        mock_read_excel.assert_called_once_with(test_file, engine="openpyxl", header=2)

    @patch("pandas.read_excel")
    def test_load_xlsx_data_mercadopago(self, mock_read_excel, xlsx_parser):
        """Test loading Mercadopago XLSX data with normal header handling"""
        # Arrange
        test_file = Path("mercadopago-test.xlsx")
        mock_df = pd.DataFrame(
            {
                "Fecha de Pago": ["2025-02-01T17:45:36Z"],
                "Tipo de Operación": ["Pago"],
                "Importe": [100.0],
            }
        )
        mock_read_excel.return_value = mock_df

        # Act
        result_df = xlsx_parser._load_xlsx_data(test_file)

        # Assert
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 1
        mock_read_excel.assert_called_once_with(test_file, engine="openpyxl")

    def test_convert_bbva_date_valid_formats(self, xlsx_parser):
        """Test BBVA date conversion from DD/MM/YY to YYYY-MM-DD"""
        # Arrange & Act & Assert
        assert xlsx_parser._convert_bbva_date("07/07/25") == "2025-07-07"
        assert xlsx_parser._convert_bbva_date("15/03/25") == "2025-03-15"
        assert xlsx_parser._convert_bbva_date("01/01/24") == "2024-01-01"
        assert xlsx_parser._convert_bbva_date("31/12/23") == "2023-12-31"

    def test_convert_bbva_date_invalid_formats(self, xlsx_parser):
        """Test BBVA date conversion with invalid formats"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            xlsx_parser._convert_bbva_date("invalid_date")

        with pytest.raises(ValueError):
            xlsx_parser._convert_bbva_date("2025-07-07")

        with pytest.raises(ValueError):
            xlsx_parser._convert_bbva_date("32/13/25")

    def test_parse_bbva_amount_usd(self, xlsx_parser):
        """Test parsing USD amounts from BBVA format"""
        # Arrange & Act
        currency, amount_str = xlsx_parser._parse_bbva_amount("USD 35,00")

        # Assert
        assert currency == Currency.USD
        assert amount_str == "35,00"

    def test_parse_bbva_amount_ars(self, xlsx_parser):
        """Test parsing ARS amounts from BBVA format"""
        # Arrange & Act
        currency, amount_str = xlsx_parser._parse_bbva_amount("$ 107.970,00")

        # Assert
        assert currency == Currency.ARS
        assert amount_str == "107.970,00"

    def test_parse_bbva_amount_default_ars(self, xlsx_parser):
        """Test parsing amounts with no currency prefix defaults to ARS"""
        # Arrange & Act
        currency, amount_str = xlsx_parser._parse_bbva_amount("1.234,56")

        # Assert
        assert currency == Currency.ARS
        assert amount_str == "1.234,56"

    def test_parse_bbva_amount_edge_cases(self, xlsx_parser):
        """Test parsing amounts with edge cases"""
        # Test with extra spaces
        currency, amount_str = xlsx_parser._parse_bbva_amount("  USD 35,00  ")
        assert currency == Currency.USD
        assert amount_str == "35,00"

        # Test with just $
        currency, amount_str = xlsx_parser._parse_bbva_amount("$ 100,00")
        assert currency == Currency.ARS
        assert amount_str == "100,00"

    @patch("pandas.read_excel")
    def test_parse_bbva_mastercard_transactions(
        self, mock_read_excel, xlsx_parser, mock_transaction_builder
    ):
        """Test parsing BBVA Mastercard transactions from DataFrame"""
        # Arrange
        mock_df = pd.DataFrame(
            {
                "Fecha y hora": ["07/07/25", "15/03/25"],
                "Movimientos": ["Onlyfans.Com", "ON FIT"],
                "Cuota": ["-", "05/06"],
                "Monto": ["USD 35,00", "$ 107.970,00"],
            }
        )

        # Configure mock to return different transactions
        transaction1 = Transaction(
            date=date(2025, 7, 7),
            description="Onlyfans.Com",
            amount=Decimal("35.00"),
            currency=Currency.USD,
            payment_method=PaymentMethod.BBVA_MASTERCARD,
        )
        transaction2 = Transaction(
            date=date(2025, 3, 15),
            description="ON FIT",
            amount=Decimal("107970.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_MASTERCARD,
        )
        mock_transaction_builder.build_from_xls_data.side_effect = [
            transaction1,
            transaction2,
        ]

        # Act
        transactions = xlsx_parser._parse_bbva_mastercard_transactions(mock_df)

        # Assert
        assert len(transactions) == 2
        assert transactions[0].description == "Onlyfans.Com"
        assert transactions[0].currency == Currency.USD
        assert transactions[1].description == "ON FIT"
        assert transactions[1].currency == Currency.ARS

        # Verify transaction builder was called correctly
        assert mock_transaction_builder.build_from_xls_data.call_count == 2

        # Check first call
        first_call = mock_transaction_builder.build_from_xls_data.call_args_list[0]
        assert first_call[1]["date_str"] == "2025-07-07"
        assert first_call[1]["description"] == "Onlyfans.Com"
        assert first_call[1]["amount_str"] == "35,00"
        assert first_call[1]["currency"] == Currency.USD
        assert first_call[1]["payment_method"] == PaymentMethod.BBVA_MASTERCARD

    @patch("pandas.read_excel")
    def test_parse_bbva_mastercard_transactions_skip_invalid(
        self, mock_read_excel, xlsx_parser, mock_transaction_builder
    ):
        """Test parsing BBVA Mastercard transactions skips invalid rows"""
        # Arrange
        mock_df = pd.DataFrame(
            {
                "Fecha y hora": ["07/07/25", "", "15/03/25"],  # Empty date
                "Movimientos": ["Onlyfans.Com", "Invalid", "ON FIT"],
                "Cuota": ["-", "05/06", "05/06"],
                "Monto": ["USD 35,00", "", "$ 107.970,00"],  # Empty amount
            }
        )

        # Configure mock to return transaction for valid rows only
        valid_transaction = Transaction(
            date=date(2025, 7, 7),
            description="Onlyfans.Com",
            amount=Decimal("35.00"),
            currency=Currency.USD,
            payment_method=PaymentMethod.BBVA_MASTERCARD,
        )
        mock_transaction_builder.build_from_xls_data.return_value = valid_transaction

        # Act
        transactions = xlsx_parser._parse_bbva_mastercard_transactions(mock_df)

        # Assert - Should only process valid rows (skip row with empty date/amount)
        assert len(transactions) == 2  # Only valid rows processed
        assert mock_transaction_builder.build_from_xls_data.call_count == 2

    @patch("pandas.read_excel")
    def test_parse_mercadopago_transactions(
        self, mock_read_excel, xlsx_parser, mock_transaction_builder
    ):
        """Test parsing Mercadopago transactions from DataFrame"""
        # Arrange
        mock_df = pd.DataFrame(
            {
                "Fecha de Pago": ["2025-02-01T17:45:36Z"],
                "Tipo de Operación": ["Pago"],
                "Importe": [100.0],
            }
        )

        mercadopago_transaction = Transaction(
            date=date(2025, 2, 1),
            description="Pago",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MERCADOPAGO,
        )
        mock_transaction_builder.build_from_xls_data.return_value = (
            mercadopago_transaction
        )

        # Act
        transactions = xlsx_parser._parse_mercadopago_transactions(mock_df)

        # Assert
        assert len(transactions) == 1
        assert transactions[0].description == "Pago"
        assert transactions[0].currency == Currency.ARS

    @patch("pandas.read_excel")
    def test_parse_transactions_routes_to_correct_parser(
        self, mock_read_excel, xlsx_parser, mock_transaction_builder
    ):
        """Test that _parse_transactions routes to correct parser based on payment method"""
        # Arrange - Create DataFrames with appropriate columns for each parser
        bbva_df = pd.DataFrame(
            {
                "Fecha y hora": ["07/07/25"],
                "Movimientos": ["Test"],
                "Cuota": ["-"],
                "Monto": ["USD 35,00"],
            }
        )

        mercadopago_df = pd.DataFrame(
            {
                "Fecha de Pago": ["2025-02-01T17:45:36Z"],
                "Tipo de Operación": ["Pago"],
                "Importe": [100.0],
            }
        )

        empty_df = pd.DataFrame({"test": ["data"]})

        # Test BBVA Mastercard routing with correct columns
        mock_transaction_builder.build_from_xls_data.return_value = Mock()
        transactions = xlsx_parser._parse_transactions(
            bbva_df, PaymentMethod.BBVA_MASTERCARD
        )
        assert len(transactions) == 1  # Should process one transaction

        # Test Mercadopago routing with correct columns
        transactions = xlsx_parser._parse_transactions(
            mercadopago_df, PaymentMethod.MERCADOPAGO
        )
        assert len(transactions) == 1  # Should process one transaction

        # Test unknown payment method
        transactions = xlsx_parser._parse_transactions(
            empty_df, PaymentMethod.BBVA_VISA
        )
        assert transactions == []  # Should return empty list for unsupported types

    @patch("pandas.read_excel")
    def test_parse_full_workflow_bbva_mastercard(
        self, mock_read_excel, xlsx_parser, mock_detector, mock_transaction_builder
    ):
        """Test full parsing workflow for BBVA Mastercard XLSX"""
        # Arrange
        test_file = Path("BBVA-Mastercard-test.xlsx")
        mock_df = pd.DataFrame(
            {
                "Fecha y hora": ["07/07/25"],
                "Movimientos": ["Onlyfans.Com"],
                "Cuota": ["-"],
                "Monto": ["USD 35,00"],
            }
        )
        mock_read_excel.return_value = mock_df

        mock_detector.detect_from_filename.return_value = PaymentMethod.BBVA_MASTERCARD

        transaction = Transaction(
            date=date(2025, 7, 7),
            description="Onlyfans.Com",
            amount=Decimal("35.00"),
            currency=Currency.USD,
            payment_method=PaymentMethod.BBVA_MASTERCARD,
        )
        mock_transaction_builder.build_from_xls_data.return_value = transaction

        # Mock file existence
        with patch.object(Path, "exists", return_value=True):
            # Act
            statement = xlsx_parser.parse(test_file)

            # Assert
            assert isinstance(statement, Statement)
            assert statement.payment_method == PaymentMethod.BBVA_MASTERCARD
            assert len(statement.transactions) == 1
            assert statement.transactions[0].description == "Onlyfans.Com"
            assert statement.transactions[0].currency == Currency.USD

    def test_parse_file_not_found(self, xlsx_parser):
        """Test parsing when file doesn't exist"""
        # Arrange
        test_file = Path("nonexistent.xlsx")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            xlsx_parser.parse(test_file)

    @patch("pandas.read_excel")
    def test_parse_empty_dataframe(self, mock_read_excel, xlsx_parser):
        """Test parsing when DataFrame is empty"""
        # Arrange
        test_file = Path("empty.xlsx")
        mock_read_excel.return_value = pd.DataFrame()

        # Mock file existence
        with patch.object(Path, "exists", return_value=True):
            # Act & Assert
            with pytest.raises(OSError):
                xlsx_parser.parse(test_file)
