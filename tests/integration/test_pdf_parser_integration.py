"""
Integration tests for PDFStatementParser with clean architecture components.

This module provides comprehensive integration tests for the PDFStatementParser
following the established testing patterns and using real PDF files for
end-to-end validation.
"""

import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from domain.builders import TransactionBuilder
from domain.utils import AmountParser, DateConverter
from infrastructure.detectors import build_default_payment_detector
from infrastructure.parsers.pdf_parser import PDFStatementParser


class TestPDFParserIntegration:
    """Integration tests for PDFStatementParser with real PDF files"""

    @pytest.fixture
    def bbva_visa_input_path(self):
        """Path to the BBVA VISA test PDF file"""
        return "tests/test_data/input/BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf"

    @pytest.fixture
    def bbva_visa_expected_csv_path(self):
        """Path to the expected BBVA VISA output CSV file"""
        return "tests/test_data/expected_output/BBVA-VISA-transactions.csv"

    @pytest.fixture
    def macro_visa_input_path(self):
        """Path to the Macro VISA test PDF file"""
        return "tests/test_data/input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"

    @pytest.fixture
    def macro_visa_expected_csv_path(self):
        """Path to the expected Macro VISA output CSV file"""
        return "tests/test_data/expected_output/MACRO-VISA-transactions.csv"

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def pdf_parser(self):
        """Create PDFStatementParser with real dependencies"""
        detector = build_default_payment_detector()
        date_converter = DateConverter()
        amount_parser = AmountParser()
        transaction_builder = TransactionBuilder(date_converter, amount_parser)

        return PDFStatementParser(detector, transaction_builder)

    @pytest.fixture
    def bbva_visa_expected_df(self, bbva_visa_expected_csv_path):
        """Load expected BBVA VISA data from CSV"""
        return pd.read_csv(bbva_visa_expected_csv_path)

    @pytest.fixture
    def macro_visa_expected_df(self, macro_visa_expected_csv_path):
        """Load expected Macro VISA data from CSV"""
        return pd.read_csv(macro_visa_expected_csv_path)

    def test_parse_bbva_visa_pdf_integration(
        self, pdf_parser, bbva_visa_input_path, bbva_visa_expected_df
    ):
        """Integration test for BBVA VISA PDF processing with new architecture"""
        # Arrange
        input_path = Path(bbva_visa_input_path)
        assert input_path.exists(), f"Input PDF file not found: {input_path}"

        # Act
        statement = pdf_parser.parse(input_path)

        # Assert
        assert statement is not None, "Statement should not be None"
        assert len(statement.transactions) > 0, "No transactions were parsed"
        assert statement.payment_method.value == "BBVA Visa", (
            "Incorrect payment method detected"
        )

        # Validate against expected data
        self._validate_statement_against_expected(statement, bbva_visa_expected_df)

    def test_parse_macro_visa_pdf_integration(
        self, pdf_parser, macro_visa_input_path, macro_visa_expected_df
    ):
        """Integration test for Macro VISA PDF processing with new architecture"""
        # Arrange
        input_path = Path(macro_visa_input_path)
        assert input_path.exists(), f"Input PDF file not found: {input_path}"

        # Act
        statement = pdf_parser.parse(input_path)

        # Assert
        assert statement is not None, "Statement should not be None"
        assert len(statement.transactions) > 0, "No transactions were parsed"
        assert statement.payment_method.value == "Macro Visa", (
            "Incorrect payment method detected"
        )

        # Validate against expected data
        self._validate_statement_against_expected(statement, macro_visa_expected_df)

    def test_bbva_visa_transaction_count(
        self, pdf_parser, bbva_visa_input_path, bbva_visa_expected_df
    ):
        """Test that the correct number of BBVA VISA transactions are parsed"""
        # Arrange
        input_path = Path(bbva_visa_input_path)
        expected_count = len(bbva_visa_expected_df)

        # Act
        statement = pdf_parser.parse(input_path)
        actual_count = len(statement.transactions)

        # Assert
        assert actual_count == expected_count, (
            f"Expected {expected_count} transactions, but got {actual_count}"
        )

    def test_macro_visa_transaction_count(
        self, pdf_parser, macro_visa_input_path, macro_visa_expected_df
    ):
        """Test that the correct number of Macro VISA transactions are parsed"""
        # Arrange
        input_path = Path(macro_visa_input_path)
        expected_count = len(macro_visa_expected_df)

        # Act
        statement = pdf_parser.parse(input_path)
        actual_count = len(statement.transactions)

        # Assert
        assert actual_count == expected_count, (
            f"Expected {expected_count} transactions, but got {actual_count}"
        )

    def test_currency_handling_bbva_visa(
        self, pdf_parser, bbva_visa_input_path, bbva_visa_expected_df
    ):
        """Test that ARS and USD currencies are handled correctly for BBVA VISA"""
        # Arrange
        input_path = Path(bbva_visa_input_path)
        expected_ars_count = len(
            bbva_visa_expected_df[bbva_visa_expected_df["Currency"] == "ARS"]
        )
        expected_usd_count = len(
            bbva_visa_expected_df[bbva_visa_expected_df["Currency"] == "USD"]
        )

        # Act
        statement = pdf_parser.parse(input_path)

        # Count by iterating through transactions
        actual_ars_count = sum(
            1 for t in statement.transactions if t.currency.value == "ARS"
        )
        actual_usd_count = sum(
            1 for t in statement.transactions if t.currency.value == "USD"
        )

        # Assert
        assert actual_ars_count == expected_ars_count, (
            f"Expected {expected_ars_count} ARS transactions, got {actual_ars_count}"
        )
        assert actual_usd_count == expected_usd_count, (
            f"Expected {expected_usd_count} USD transactions, got {actual_usd_count}"
        )

        # Verify all currencies are valid
        valid_currencies = {"ARS", "USD"}
        actual_currencies = {t.currency.value for t in statement.transactions}
        assert actual_currencies.issubset(valid_currencies), (
            f"Invalid currencies found: {actual_currencies - valid_currencies}"
        )

    def test_amount_totals_bbva_visa(
        self, pdf_parser, bbva_visa_input_path, bbva_visa_expected_df
    ):
        """Test that amount totals match expected values for BBVA VISA"""
        # Arrange
        input_path = Path(bbva_visa_input_path)
        expected_ars_total = bbva_visa_expected_df[
            bbva_visa_expected_df["Currency"] == "ARS"
        ]["Amount"].sum()
        expected_usd_total = bbva_visa_expected_df[
            bbva_visa_expected_df["Currency"] == "USD"
        ]["Amount"].sum()

        # Act
        statement = pdf_parser.parse(input_path)

        # Calculate actual totals
        actual_ars_total = sum(
            float(t.amount) for t in statement.transactions if t.currency.value == "ARS"
        )
        actual_usd_total = sum(
            float(t.amount) for t in statement.transactions if t.currency.value == "USD"
        )

        # Assert
        assert abs(actual_ars_total - expected_ars_total) < 0.01, (
            f"ARS total mismatch: expected {expected_ars_total:.2f}, got {actual_ars_total:.2f}"
        )
        assert abs(actual_usd_total - expected_usd_total) < 0.01, (
            f"USD total mismatch: expected {expected_usd_total:.2f}, got {actual_usd_total:.2f}"
        )

    def test_date_range_and_format_bbva_visa(
        self, pdf_parser, bbva_visa_input_path, bbva_visa_expected_df
    ):
        """Test that dates are in the correct range and format for BBVA VISA"""
        # Arrange
        input_path = Path(bbva_visa_input_path)
        expected_dates = pd.to_datetime(bbva_visa_expected_df["Date"])
        expected_min_date = expected_dates.min()
        expected_max_date = expected_dates.max()

        # Act
        statement = pdf_parser.parse(input_path)
        actual_dates = [t.date for t in statement.transactions]
        actual_min_date = pd.Timestamp(min(actual_dates))
        actual_max_date = pd.Timestamp(max(actual_dates))

        # Assert
        assert actual_min_date == expected_min_date, (
            f"Minimum date mismatch: expected {expected_min_date}, got {actual_min_date}"
        )
        assert actual_max_date == expected_max_date, (
            f"Maximum date mismatch: expected {expected_max_date}, got {actual_max_date}"
        )

        # Verify date format (should be date objects)
        for transaction in statement.transactions:
            assert hasattr(transaction.date, "year"), "Date should be a date object"
            assert hasattr(transaction.date, "month"), "Date should be a date object"
            assert hasattr(transaction.date, "day"), "Date should be a date object"

    def test_payment_method_consistency_bbva_visa(
        self, pdf_parser, bbva_visa_input_path
    ):
        """Test that all BBVA VISA transactions have the correct payment method"""
        # Arrange
        input_path = Path(bbva_visa_input_path)
        expected_payment_method = "BBVA Visa"

        # Act
        statement = pdf_parser.parse(input_path)

        # Assert
        assert statement.payment_method.value == expected_payment_method, (
            f"Expected payment method '{expected_payment_method}', got '{statement.payment_method.value}'"
        )

        # Verify all transactions have consistent payment method
        for transaction in statement.transactions:
            assert transaction.payment_method.value == expected_payment_method, (
                f"Transaction has inconsistent payment method: {transaction.payment_method.value}"
            )

    def test_specific_transaction_types_bbva_visa(
        self, pdf_parser, bbva_visa_input_path, bbva_visa_expected_df
    ):
        """Test specific transaction types are parsed correctly for BBVA VISA"""
        # Arrange
        input_path = Path(bbva_visa_input_path)

        # Act
        statement = pdf_parser.parse(input_path)

        # Test payment transactions
        payment_transactions = [
            t for t in statement.transactions if t.description == "SU PAGO EN PESOS"
        ]
        expected_payments = bbva_visa_expected_df[
            bbva_visa_expected_df["Description"] == "SU PAGO EN PESOS"
        ]
        assert len(payment_transactions) == len(expected_payments), (
            f"Expected {len(expected_payments)} payment transactions, got {len(payment_transactions)}"
        )

        # Test adjustment transactions
        adjustment_transactions = [
            t
            for t in statement.transactions
            if t.description == "AJUSTE P/DESCNTO. EN COMERCIO"
        ]
        expected_adjustments = bbva_visa_expected_df[
            bbva_visa_expected_df["Description"] == "AJUSTE P/DESCNTO. EN COMERCIO"
        ]
        assert len(adjustment_transactions) == len(expected_adjustments), (
            f"Expected {len(expected_adjustments)} adjustment transactions, got {len(adjustment_transactions)}"
        )

        # Test tax transactions
        tax_keywords = ["IMPUESTO", "IIBB", "IVA", "DB.RG", "DB.IMPUESTO"]
        for keyword in tax_keywords:
            result_tax = [t for t in statement.transactions if keyword in t.description]
            expected_tax = bbva_visa_expected_df[
                bbva_visa_expected_df["Description"].str.contains(keyword, na=False)
            ]
            assert len(result_tax) == len(expected_tax), (
                f"Mismatch in {keyword} transactions: expected {len(expected_tax)}, got {len(result_tax)}"
            )

    def test_negative_amounts_bbva_visa(self, pdf_parser, bbva_visa_input_path):
        """Test that payments and adjustments have negative amounts for BBVA VISA"""
        # Arrange
        input_path = Path(bbva_visa_input_path)

        # Act
        statement = pdf_parser.parse(input_path)

        # Test payment transactions have negative amounts
        payments = [
            t for t in statement.transactions if t.description == "SU PAGO EN PESOS"
        ]
        for payment in payments:
            assert payment.amount < 0, (
                f"Payment transaction should have negative amount, got {payment.amount}"
            )

        # Test adjustment transactions have negative amounts
        adjustments = [
            t
            for t in statement.transactions
            if t.description == "AJUSTE P/DESCNTO. EN COMERCIO"
        ]
        for adjustment in adjustments:
            assert adjustment.amount < 0, (
                f"Adjustment transaction should have negative amount, got {adjustment.amount}"
            )

    def test_parser_can_parse_method(self, pdf_parser):
        """Test that parser correctly identifies PDF files"""
        # Test PDF files
        assert pdf_parser.can_parse(Path("statement.pdf")) is True
        assert pdf_parser.can_parse(Path("STATEMENT.PDF")) is True

        # Test non-PDF files
        assert pdf_parser.can_parse(Path("statement.xls")) is False
        assert pdf_parser.can_parse(Path("statement.csv")) is False
        assert pdf_parser.can_parse(Path("statement.xlsx")) is False

    def test_parser_supported_extensions(self, pdf_parser):
        """Test that parser returns correct supported extensions"""
        extensions = pdf_parser.get_supported_extensions()
        assert extensions == {".pdf"}

    def _validate_statement_against_expected(self, statement, expected_df):
        """Validate statement data integrity against expected DataFrame"""
        # Convert statement to comparable format
        statement_data = []
        for transaction in statement.transactions:
            statement_data.append(
                {
                    "Date": transaction.date.strftime("%Y-%m-%d"),
                    "Description": transaction.description,
                    "Currency": transaction.currency.value,
                    "Amount": float(transaction.amount),
                    "Payment Method": transaction.payment_method.value,
                }
            )

        result_df = pd.DataFrame(statement_data)

        # Validate transaction count
        assert len(result_df) == len(expected_df), (
            f"Transaction count mismatch: expected {len(expected_df)}, got {len(result_df)}"
        )

        # Validate currency distribution
        expected_ars_count = len(expected_df[expected_df["Currency"] == "ARS"])
        expected_usd_count = len(expected_df[expected_df["Currency"] == "USD"])
        actual_ars_count = len(result_df[result_df["Currency"] == "ARS"])
        actual_usd_count = len(result_df[result_df["Currency"] == "USD"])

        assert actual_ars_count == expected_ars_count, (
            f"ARS transaction count mismatch: expected {expected_ars_count}, got {actual_ars_count}"
        )
        assert actual_usd_count == expected_usd_count, (
            f"USD transaction count mismatch: expected {expected_usd_count}, got {actual_usd_count}"
        )

        # Validate amount totals
        expected_ars_total = expected_df[expected_df["Currency"] == "ARS"][
            "Amount"
        ].sum()
        expected_usd_total = expected_df[expected_df["Currency"] == "USD"][
            "Amount"
        ].sum()
        actual_ars_total = result_df[result_df["Currency"] == "ARS"]["Amount"].sum()
        actual_usd_total = result_df[result_df["Currency"] == "USD"]["Amount"].sum()

        assert abs(actual_ars_total - expected_ars_total) < 0.01, (
            f"ARS total mismatch: expected {expected_ars_total:.2f}, got {actual_ars_total:.2f}"
        )
        assert abs(actual_usd_total - expected_usd_total) < 0.01, (
            f"USD total mismatch: expected {expected_usd_total:.2f}, got {actual_usd_total:.2f}"
        )

        # Validate date range
        result_dates = pd.to_datetime(result_df["Date"])
        expected_dates = pd.to_datetime(expected_df["Date"])

        assert result_dates.min() == expected_dates.min(), (
            f"Min date mismatch: expected {expected_dates.min()}, got {result_dates.min()}"
        )
        assert result_dates.max() == expected_dates.max(), (
            f"Max date mismatch: expected {expected_dates.max()}, got {result_dates.max()}"
        )

        # Validate special transaction types
        special_descriptions = ["SU PAGO EN PESOS", "AJUSTE P/DESCNTO. EN COMERCIO"]
        for desc in special_descriptions:
            expected_count = len(expected_df[expected_df["Description"] == desc])
            actual_count = len(result_df[result_df["Description"] == desc])
            assert actual_count == expected_count, (
                f"Special transaction '{desc}' count mismatch: expected {expected_count}, got {actual_count}"
            )
