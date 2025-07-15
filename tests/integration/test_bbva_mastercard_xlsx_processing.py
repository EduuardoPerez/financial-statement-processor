"""
Integration tests for BBVA Mastercard XLSX processing.

This module provides integration tests for the BBVA Mastercard XLSX parser
with real files, testing the dual-format support and data processing accuracy.
"""

import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from domain.builders import TransactionBuilder
from domain.models import PaymentMethod
from domain.utils import AmountParser, DateConverter
from infrastructure.detectors import build_default_payment_detector
from infrastructure.parsers.xlsx_parser import XLSXStatementParser


class TestBBVAMastercardXLSXProcessing:
    """Integration tests for BBVA Mastercard XLSX processing"""

    @pytest.fixture
    def input_xlsx_path(self):
        """Path to the test XLSX file"""
        return Path("tests/test_data/input/BBVA-Mastercard-Últimos movimientos.xlsx")

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def xlsx_parser(self):
        """Create XLSXStatementParser with real dependencies"""
        detector = build_default_payment_detector()
        transaction_builder = TransactionBuilder(DateConverter(), AmountParser())
        return XLSXStatementParser(detector, transaction_builder)

    def test_xlsx_file_exists(self, input_xlsx_path):
        """Test that the required XLSX fixture file exists"""
        assert input_xlsx_path.exists(), (
            f"XLSX fixture file not found at {input_xlsx_path}"
        )
        assert input_xlsx_path.is_file(), (
            f"Path exists but is not a file: {input_xlsx_path}"
        )
        assert input_xlsx_path.suffix.lower() == ".xlsx", (
            f"File is not an XLSX: {input_xlsx_path}"
        )

    def test_parse_bbva_mastercard_xlsx_integration(self, xlsx_parser, input_xlsx_path):
        """Integration test for complete BBVA Mastercard XLSX parsing"""
        # Act
        statement = xlsx_parser.parse(input_xlsx_path)

        # Assert
        assert statement.payment_method == PaymentMethod.BBVA_MASTERCARD
        assert len(statement.transactions) == 2, (
            f"Expected 2 transactions, got {len(statement.transactions)}"
        )

        # Validate transactions
        transactions = statement.transactions
        assert transactions[0].description == "Onlyfans.Com"
        assert transactions[0].currency.value == "USD"
        assert float(transactions[0].amount) == 35.00
        assert transactions[0].date.strftime("%Y-%m-%d") == "2025-07-07"

        assert transactions[1].description == "ON FIT"
        assert transactions[1].currency.value == "ARS"
        assert float(transactions[1].amount) == 107970.00
        assert transactions[1].date.strftime("%Y-%m-%d") == "2025-03-15"

    def test_currency_detection_accuracy(self, xlsx_parser, input_xlsx_path):
        """Test that currency detection works correctly for both USD and ARS"""
        # Act
        statement = xlsx_parser.parse(input_xlsx_path)

        # Assert
        currencies = [t.currency.value for t in statement.transactions]
        assert "USD" in currencies, "USD currency not detected"
        assert "ARS" in currencies, "ARS currency not detected"

        # Validate specific currency assignments
        usd_transactions = [
            t for t in statement.transactions if t.currency.value == "USD"
        ]
        ars_transactions = [
            t for t in statement.transactions if t.currency.value == "ARS"
        ]

        assert len(usd_transactions) == 1, (
            f"Expected 1 USD transaction, got {len(usd_transactions)}"
        )
        assert len(ars_transactions) == 1, (
            f"Expected 1 ARS transaction, got {len(ars_transactions)}"
        )

    def test_date_conversion_accuracy(self, xlsx_parser, input_xlsx_path):
        """Test that DD/MM/YY dates are converted correctly to YYYY-MM-DD"""
        # Act
        statement = xlsx_parser.parse(input_xlsx_path)

        # Assert
        dates = [t.date.strftime("%Y-%m-%d") for t in statement.transactions]
        expected_dates = ["2025-07-07", "2025-03-15"]

        assert sorted(dates) == sorted(expected_dates), (
            f"Expected dates {expected_dates}, got {dates}"
        )

    def test_amount_parsing_accuracy(self, xlsx_parser, input_xlsx_path):
        """Test that European format amounts are parsed correctly"""
        # Act
        statement = xlsx_parser.parse(input_xlsx_path)

        # Assert
        amounts = [float(t.amount) for t in statement.transactions]
        expected_amounts = [35.00, 107970.00]

        assert sorted(amounts) == sorted(expected_amounts), (
            f"Expected amounts {expected_amounts}, got {amounts}"
        )

    def test_payment_method_detection(self, xlsx_parser, input_xlsx_path):
        """Test that payment method is correctly detected from filename"""
        # Act
        statement = xlsx_parser.parse(input_xlsx_path)

        # Assert
        assert statement.payment_method == PaymentMethod.BBVA_MASTERCARD

        # All transactions should have the same payment method
        for transaction in statement.transactions:
            assert transaction.payment_method == PaymentMethod.BBVA_MASTERCARD

    def test_filename_variations(self, xlsx_parser, temp_output_dir):
        """Test that various BBVA Mastercard filename patterns are detected correctly"""
        # Arrange
        input_file = Path(
            "tests/test_data/input/BBVA-Mastercard-Últimos movimientos.xlsx"
        )
        if not input_file.exists():
            pytest.skip("Test file not found")

        test_filenames = [
            "BBVA-Mastercard-test.xlsx",
            "BBVA-MASTERCARD-movements.xlsx",
            "bbva-mastercard-data.xlsx",
            "BBVA-Mastercard-Últimos-movimientos.xlsx",
        ]

        for filename in test_filenames:
            # Create a temporary file with the test filename
            test_file = temp_output_dir / filename
            shutil.copy(input_file, test_file)

            # Act
            statement = xlsx_parser.parse(test_file)

            # Assert
            assert statement.payment_method == PaymentMethod.BBVA_MASTERCARD, (
                f"Wrong payment method detected for filename {filename}: {statement.payment_method}"
            )

    def test_data_integrity_with_real_file(self, xlsx_parser, input_xlsx_path):
        """Test complete data integrity with the real BBVA Mastercard XLSX file"""
        # Act
        statement = xlsx_parser.parse(input_xlsx_path)

        # Assert data integrity
        assert len(statement.transactions) == 2, "Should have exactly 2 transactions"

        # Validate first transaction (Onlyfans.Com)
        first_transaction = statement.transactions[0]
        assert first_transaction.description == "Onlyfans.Com"
        assert first_transaction.currency.value == "USD"
        assert float(first_transaction.amount) == 35.00
        assert first_transaction.date.strftime("%Y-%m-%d") == "2025-07-07"
        assert first_transaction.payment_method == PaymentMethod.BBVA_MASTERCARD

        # Validate second transaction (ON FIT)
        second_transaction = statement.transactions[1]
        assert second_transaction.description == "ON FIT"
        assert second_transaction.currency.value == "ARS"
        assert float(second_transaction.amount) == 107970.00
        assert second_transaction.date.strftime("%Y-%m-%d") == "2025-03-15"
        assert second_transaction.payment_method == PaymentMethod.BBVA_MASTERCARD

    def test_parser_can_handle_file(self, xlsx_parser, input_xlsx_path):
        """Test that the parser correctly identifies it can handle the file"""
        # Act & Assert
        assert xlsx_parser.can_parse(input_xlsx_path), (
            "Parser should be able to handle BBVA Mastercard XLSX files"
        )

    def test_supported_extensions(self, xlsx_parser):
        """Test that the parser reports correct supported extensions"""
        # Act
        extensions = xlsx_parser.get_supported_extensions()

        # Assert
        assert ".xlsx" in extensions, "Parser should support .xlsx files"

    def test_error_handling_nonexistent_file(self, xlsx_parser):
        """Test error handling when file doesn't exist"""
        # Arrange
        nonexistent_file = Path("nonexistent.xlsx")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            xlsx_parser.parse(nonexistent_file)

    def test_raw_data_loading(self, xlsx_parser, input_xlsx_path):
        """Test that raw XLSX data is loaded correctly"""
        # Act
        df = xlsx_parser._load_xlsx_data(input_xlsx_path)

        # Assert
        assert isinstance(df, pd.DataFrame), "Should return a DataFrame"
        assert len(df) == 2, "Should have 2 rows of data"
        assert "Fecha y hora" in df.columns, "Should have 'Fecha y hora' column"
        assert "Movimientos" in df.columns, "Should have 'Movimientos' column"
        assert "Monto" in df.columns, "Should have 'Monto' column"

    def test_bbva_date_conversion_methods(self, xlsx_parser):
        """Test BBVA-specific date conversion methods"""
        # Test various date formats
        test_cases = [
            ("07/07/25", "2025-07-07"),
            ("15/03/25", "2025-03-15"),
            ("01/01/24", "2024-01-01"),
            ("31/12/23", "2023-12-31"),
        ]

        for input_date, expected_output in test_cases:
            result = xlsx_parser._convert_bbva_date(input_date)
            assert result == expected_output, (
                f"Date conversion failed for {input_date}: expected {expected_output}, got {result}"
            )

    def test_bbva_amount_parsing_methods(self, xlsx_parser):
        """Test BBVA-specific amount parsing methods"""
        # Test various amount formats
        test_cases = [
            ("USD 35,00", ("USD", "35,00")),
            ("$ 107.970,00", ("ARS", "107.970,00")),
            ("1.234,56", ("ARS", "1.234,56")),  # Default to ARS
            ("  USD 35,00  ", ("USD", "35,00")),  # With spaces
        ]

        for input_amount, expected_output in test_cases:
            result = xlsx_parser._parse_bbva_amount(input_amount)
            expected_currency, expected_amount = expected_output
            result_currency, result_amount = result

            assert result_currency.value == expected_currency, (
                f"Currency parsing failed for {input_amount}"
            )
            assert result_amount == expected_amount, (
                f"Amount parsing failed for {input_amount}"
            )

    def test_performance_with_real_file(self, xlsx_parser, input_xlsx_path):
        """Test that processing performance is acceptable with real file"""
        import time

        # Act
        start_time = time.time()
        statement = xlsx_parser.parse(input_xlsx_path)
        end_time = time.time()

        # Assert
        processing_time = end_time - start_time
        assert processing_time < 2.0, (
            f"Processing took too long: {processing_time:.2f} seconds (max 2.0 seconds)"
        )
        assert len(statement.transactions) == 2, "Should process all transactions"
