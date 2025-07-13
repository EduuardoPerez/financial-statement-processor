"""
Unit tests for balance extraction implementations.

This module tests the concrete balance extractor implementations and the
registry service that manages them.
"""

from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

from domain.models import PaymentMethod
from infrastructure.extractors import (
    BalanceExtractionService,
    CSVBalanceExtractor,
    PDFBalanceExtractor,
    XLSXBalanceExtractor,
    build_default_balance_service,
)


class TestPDFBalanceExtractor:
    """Test PDFBalanceExtractor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = PDFBalanceExtractor()

    def test_can_extract_supported_payment_methods(self):
        """Test can_extract returns True for PDF-based payment methods."""
        pdf_methods = [
            PaymentMethod.BBVA_VISA,
            PaymentMethod.BBVA_MASTERCARD,
            PaymentMethod.MACRO_VISA,
        ]

        for method in pdf_methods:
            assert self.extractor.can_extract(method) is True

    def test_can_extract_unsupported_payment_methods(self):
        """Test can_extract returns False for non-PDF payment methods."""
        non_pdf_methods = [
            PaymentMethod.BBVA_ACCOUNT,
            PaymentMethod.MACRO_ACCOUNT,
            PaymentMethod.MERCADOPAGO,
        ]

        for method in non_pdf_methods:
            assert self.extractor.can_extract(method) is False

    def test_extract_balance_bbva_mastercard_pattern1(self):
        """Test BBVA Mastercard balance extraction with pattern 1."""
        content = """
        Some text before
        SALDO ACTUAL $ 1.234,56 more text SALDO ACTUAL U$S 567,89
        Some text after
        """

        result = self.extractor.extract_balance(content, PaymentMethod.BBVA_MASTERCARD)

        assert result["ars"] == Decimal("1234.56")
        assert result["usd"] == Decimal("567.89")

    def test_extract_balance_bbva_mastercard_pattern2(self):
        """Test BBVA Mastercard balance extraction with pattern 2."""
        content = """
        Some text
        01-Jan-25 31-Jan-25 1.500,00 800,25 100,50
        More text
        """

        result = self.extractor.extract_balance(content, PaymentMethod.BBVA_MASTERCARD)

        assert result["ars"] == Decimal("1500.00")
        assert result["usd"] == Decimal("800.25")

    def test_extract_balance_bbva_mastercard_no_match(self):
        """Test BBVA Mastercard balance extraction with no matches."""
        content = "No balance information here"

        result = self.extractor.extract_balance(content, PaymentMethod.BBVA_MASTERCARD)

        assert result["ars"] == Decimal("0.0")
        assert result["usd"] == Decimal("0.0")

    def test_extract_balance_standard_format_both_currencies(self):
        """Test standard format extraction with both ARS and USD."""
        content = """
        Some content
        SALDO ACTUAL $ 2.500,75 U$S 1.200,50
        More content
        """

        result = self.extractor.extract_balance(content, PaymentMethod.BBVA_VISA)

        assert result["ars"] == Decimal("2500.75")
        assert result["usd"] == Decimal("1200.50")

    def test_extract_balance_standard_format_ars_only(self):
        """Test standard format extraction with ARS only."""
        content = """
        Some content
        SALDO ACTUAL $ 3.750,25
        More content
        """

        result = self.extractor.extract_balance(content, PaymentMethod.MACRO_VISA)

        assert result["ars"] == Decimal("3750.25")
        assert result["usd"] == Decimal("0.0")

    def test_extract_balance_standard_format_no_match(self):
        """Test standard format extraction with no matches."""
        content = "Random content without balance info"

        result = self.extractor.extract_balance(content, PaymentMethod.BBVA_VISA)

        assert result["ars"] == Decimal("0.0")
        assert result["usd"] == Decimal("0.0")

    def test_parse_european_amount_with_thousands_separator(self):
        """Test European amount parsing with thousands separator."""
        result = self.extractor._parse_european_amount("1.234,56")
        assert result == Decimal("1234.56")

    def test_parse_european_amount_with_comma_only(self):
        """Test European amount parsing with comma decimal separator only."""
        result = self.extractor._parse_european_amount("1234,56")
        assert result == Decimal("1234.56")

    def test_parse_european_amount_with_dot_only(self):
        """Test European amount parsing with dot as decimal separator."""
        result = self.extractor._parse_european_amount("1234.56")
        assert result == Decimal("1234.56")

    def test_parse_european_amount_invalid_format(self):
        """Test European amount parsing with invalid format."""
        result = self.extractor._parse_european_amount("invalid")
        assert result == Decimal("0.0")

    def test_parse_european_amount_none_input(self):
        """Test European amount parsing with None input."""
        result = self.extractor._parse_european_amount(None)
        assert result == Decimal("0.0")


class TestCSVBalanceExtractor:
    """Test CSVBalanceExtractor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = CSVBalanceExtractor()

    def test_can_extract_supported_payment_methods(self):
        """Test can_extract returns True for CSV-based payment methods."""
        csv_methods = [PaymentMethod.BBVA_VISA, PaymentMethod.MACRO_VISA]

        for method in csv_methods:
            assert self.extractor.can_extract(method) is True

    def test_can_extract_unsupported_payment_methods(self):
        """Test can_extract returns False for non-CSV payment methods."""
        non_csv_methods = [
            PaymentMethod.BBVA_MASTERCARD,
            PaymentMethod.BBVA_ACCOUNT,
            PaymentMethod.MACRO_ACCOUNT,
            PaymentMethod.MERCADOPAGO,
        ]

        for method in non_csv_methods:
            assert self.extractor.can_extract(method) is False

    @patch("pandas.read_csv")
    def test_extract_balance_success(self, mock_read_csv):
        """Test successful CSV balance extraction."""
        # Mock DataFrame with transaction data
        mock_df = pd.DataFrame({"Importe": ["100.50", "200.75", "150.25"]})
        mock_read_csv.return_value = mock_df

        result = self.extractor.extract_balance("test.csv", PaymentMethod.BBVA_VISA)

        assert result["ars"] == Decimal("451.50")  # 100.50 + 200.75 + 150.25
        assert result["usd"] == Decimal("0.0")
        mock_read_csv.assert_called_once_with(Path("test.csv"), sep=";")

    @patch("pandas.read_csv")
    def test_extract_balance_with_nan_values(self, mock_read_csv):
        """Test CSV balance extraction with NaN values."""
        mock_df = pd.DataFrame({"Importe": ["100.50", "nan", "200.75", ""]})
        mock_read_csv.return_value = mock_df

        result = self.extractor.extract_balance("test.csv", PaymentMethod.MACRO_VISA)

        assert result["ars"] == Decimal("301.25")  # Only valid amounts summed
        assert result["usd"] == Decimal("0.0")

    @patch("pandas.read_csv")
    def test_extract_balance_with_invalid_amounts(self, mock_read_csv):
        """Test CSV balance extraction with invalid amount formats."""
        mock_df = pd.DataFrame({"Importe": ["100.50", "invalid", "200.75", "text"]})
        mock_read_csv.return_value = mock_df

        result = self.extractor.extract_balance("test.csv", PaymentMethod.BBVA_VISA)

        assert result["ars"] == Decimal("301.25")  # Only valid amounts summed
        assert result["usd"] == Decimal("0.0")

    @patch("pandas.read_csv")
    def test_extract_balance_file_error(self, mock_read_csv):
        """Test CSV balance extraction with file reading error."""
        mock_read_csv.side_effect = Exception("File not found")

        result = self.extractor.extract_balance(
            "nonexistent.csv", PaymentMethod.BBVA_VISA
        )

        assert result["ars"] == Decimal("0.0")
        assert result["usd"] == Decimal("0.0")

    @patch("pandas.read_csv")
    def test_extract_balance_empty_dataframe(self, mock_read_csv):
        """Test CSV balance extraction with empty DataFrame."""
        mock_df = pd.DataFrame({"Importe": []})
        mock_read_csv.return_value = mock_df

        result = self.extractor.extract_balance("empty.csv", PaymentMethod.MACRO_VISA)

        assert result["ars"] == Decimal("0.0")
        assert result["usd"] == Decimal("0.0")


class TestXLSXBalanceExtractor:
    """Test XLSXBalanceExtractor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = XLSXBalanceExtractor()

    def test_can_extract_supported_payment_method(self):
        """Test can_extract returns True for MERCADOPAGO."""
        assert self.extractor.can_extract(PaymentMethod.MERCADOPAGO) is True

    def test_can_extract_unsupported_payment_methods(self):
        """Test can_extract returns False for non-XLSX payment methods."""
        non_xlsx_methods = [
            PaymentMethod.BBVA_VISA,
            PaymentMethod.BBVA_MASTERCARD,
            PaymentMethod.BBVA_ACCOUNT,
            PaymentMethod.MACRO_VISA,
            PaymentMethod.MACRO_ACCOUNT,
        ]

        for method in non_xlsx_methods:
            assert self.extractor.can_extract(method) is False

    @patch("pandas.read_excel")
    def test_extract_balance_success(self, mock_read_excel):
        """Test successful XLSX balance extraction."""
        mock_df = pd.DataFrame({"Importe": [100.50, 200.75, 150.25]})
        mock_read_excel.return_value = mock_df

        result = self.extractor.extract_balance("test.xlsx", PaymentMethod.MERCADOPAGO)

        assert result["ars"] == Decimal("451.50")
        assert result["usd"] == Decimal("0.0")
        mock_read_excel.assert_called_once_with(Path("test.xlsx"))

    @patch("pandas.read_excel")
    def test_extract_balance_with_nan_values(self, mock_read_excel):
        """Test XLSX balance extraction with NaN values."""
        import numpy as np

        mock_df = pd.DataFrame({"Importe": [100.50, np.nan, 200.75, np.nan]})
        mock_read_excel.return_value = mock_df

        result = self.extractor.extract_balance("test.xlsx", PaymentMethod.MERCADOPAGO)

        assert result["ars"] == Decimal("301.25")
        assert result["usd"] == Decimal("0.0")

    @patch("pandas.read_excel")
    def test_extract_balance_with_invalid_amounts(self, mock_read_excel):
        """Test XLSX balance extraction with invalid amount formats."""
        mock_df = pd.DataFrame({"Importe": [100.50, "invalid", 200.75, "text"]})
        mock_read_excel.return_value = mock_df

        result = self.extractor.extract_balance("test.xlsx", PaymentMethod.MERCADOPAGO)

        assert result["ars"] == Decimal("301.25")
        assert result["usd"] == Decimal("0.0")

    @patch("pandas.read_excel")
    def test_extract_balance_file_error(self, mock_read_excel):
        """Test XLSX balance extraction with file reading error."""
        mock_read_excel.side_effect = Exception("File not found")

        result = self.extractor.extract_balance(
            "nonexistent.xlsx", PaymentMethod.MERCADOPAGO
        )

        assert result["ars"] == Decimal("0.0")
        assert result["usd"] == Decimal("0.0")

    @patch("pandas.read_excel")
    def test_extract_balance_empty_dataframe(self, mock_read_excel):
        """Test XLSX balance extraction with empty DataFrame."""
        mock_df = pd.DataFrame({"Importe": []})
        mock_read_excel.return_value = mock_df

        result = self.extractor.extract_balance("empty.xlsx", PaymentMethod.MERCADOPAGO)

        assert result["ars"] == Decimal("0.0")
        assert result["usd"] == Decimal("0.0")


class TestBalanceExtractionService:
    """Test BalanceExtractionService registry functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = BalanceExtractionService()
        self.mock_extractor = Mock()

    def test_register_extractor(self):
        """Test registering an extractor."""
        self.service.register_extractor(self.mock_extractor)

        assert self.mock_extractor in self.service._extractors

    def test_extract_balance_with_matching_extractor(self):
        """Test balance extraction with matching extractor."""
        self.mock_extractor.can_extract.return_value = True
        self.mock_extractor.extract_balance.return_value = {
            "ars": Decimal("100.0"),
            "usd": Decimal("50.0"),
        }
        self.service.register_extractor(self.mock_extractor)

        result = self.service.extract_balance("content", PaymentMethod.BBVA_VISA)

        assert result == {"ars": Decimal("100.0"), "usd": Decimal("50.0")}
        self.mock_extractor.can_extract.assert_called_once_with(PaymentMethod.BBVA_VISA)
        self.mock_extractor.extract_balance.assert_called_once_with(
            "content", PaymentMethod.BBVA_VISA
        )

    def test_extract_balance_with_no_matching_extractor(self):
        """Test balance extraction with no matching extractor."""
        self.mock_extractor.can_extract.return_value = False
        self.service.register_extractor(self.mock_extractor)

        result = self.service.extract_balance("content", PaymentMethod.BBVA_VISA)

        assert result is None
        self.mock_extractor.can_extract.assert_called_once_with(PaymentMethod.BBVA_VISA)
        self.mock_extractor.extract_balance.assert_not_called()

    def test_extract_balance_multiple_extractors_first_match(self):
        """Test balance extraction with multiple extractors, first matches."""
        extractor1 = Mock()
        extractor2 = Mock()

        extractor1.can_extract.return_value = True
        extractor1.extract_balance.return_value = {
            "ars": Decimal("100.0"),
            "usd": Decimal("0.0"),
        }
        extractor2.can_extract.return_value = True
        extractor2.extract_balance.return_value = {
            "ars": Decimal("200.0"),
            "usd": Decimal("0.0"),
        }

        self.service.register_extractor(extractor1)
        self.service.register_extractor(extractor2)

        result = self.service.extract_balance("content", PaymentMethod.BBVA_VISA)

        # Should use first matching extractor
        assert result == {"ars": Decimal("100.0"), "usd": Decimal("0.0")}
        extractor1.can_extract.assert_called_once()
        extractor1.extract_balance.assert_called_once()
        extractor2.can_extract.assert_not_called()

    def test_extract_balance_multiple_extractors_second_match(self):
        """Test balance extraction with multiple extractors, second matches."""
        extractor1 = Mock()
        extractor2 = Mock()

        extractor1.can_extract.return_value = False
        extractor2.can_extract.return_value = True
        extractor2.extract_balance.return_value = {
            "ars": Decimal("200.0"),
            "usd": Decimal("0.0"),
        }

        self.service.register_extractor(extractor1)
        self.service.register_extractor(extractor2)

        result = self.service.extract_balance("content", PaymentMethod.BBVA_VISA)

        assert result == {"ars": Decimal("200.0"), "usd": Decimal("0.0")}
        extractor1.can_extract.assert_called_once()
        extractor2.can_extract.assert_called_once()
        extractor2.extract_balance.assert_called_once()

    def test_extract_balance_empty_service(self):
        """Test balance extraction with no registered extractors."""
        result = self.service.extract_balance("content", PaymentMethod.BBVA_VISA)

        assert result is None


class TestBuildDefaultBalanceService:
    """Test build_default_balance_service factory function."""

    def test_build_default_service(self):
        """Test building default balance service with all extractors."""
        service = build_default_balance_service()

        assert len(service._extractors) == 3

        # Check that all extractor types are registered
        extractor_types = [type(extractor) for extractor in service._extractors]
        assert PDFBalanceExtractor in extractor_types
        assert CSVBalanceExtractor in extractor_types
        assert XLSXBalanceExtractor in extractor_types

    def test_default_service_can_handle_all_payment_methods(self):
        """Test that default service can handle all relevant payment methods."""
        service = build_default_balance_service()

        # Test PDF methods
        for method in [
            PaymentMethod.BBVA_VISA,
            PaymentMethod.BBVA_MASTERCARD,
            PaymentMethod.MACRO_VISA,
        ]:
            result = service.extract_balance("test content", method)
            assert result is not None  # Should find an extractor

        # Test MERCADOPAGO
        result = service.extract_balance("test.xlsx", PaymentMethod.MERCADOPAGO)
        assert result is not None  # Should find XLSX extractor

        # Test that it returns proper structure
        assert isinstance(result, dict)
        assert "ars" in result
        assert "usd" in result
