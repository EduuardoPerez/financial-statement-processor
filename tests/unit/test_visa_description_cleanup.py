"""
Tests for Visa transaction description cleanup functionality.

This module tests that reference numbers are properly removed from Visa
transaction descriptions while maintaining all parsing functionality.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from domain.builders import TransactionBuilder
from domain.models import Currency, PaymentMethod
from domain.utils import AmountParser, DateConverter
from infrastructure.parsers.pdf_parser import PDFStatementParser


class TestVisaDescriptionCleanup:
    """Test cases for cleaning up Visa transaction descriptions."""

    @pytest.fixture
    def mock_detector(self):
        """Mock payment method detector."""
        detector = Mock()
        detector.detect_from_content.return_value = PaymentMethod.BBVA_VISA
        return detector

    @pytest.fixture
    def transaction_builder(self):
        """Transaction builder with real utilities."""
        return TransactionBuilder(DateConverter(), AmountParser())

    @pytest.fixture
    def parser(self, mock_detector, transaction_builder):
        """PDF parser instance for testing."""
        return PDFStatementParser(mock_detector, transaction_builder)

    def test_reference_pattern_detection_with_all_suffixes(self, parser):
        """Test that the regex pattern correctly detects all reference suffixes."""
        # Test data with different reference patterns
        test_lines = [
            "05.06.25 005302* ON FIT Cuota 06/06",
            "18.01.25 001320* SANDRULI SRL",
            "19.01.25 000001* AUBASA 960009587459301",
            "30.01.25 071512K MERPAGO*THOMAS",
            "01.02.25 891733K MERPAGO*LUCKY13",
            "04.02.25 093709Q NETFLIX.COM 42785628363430465",
            "13.02.25 994537* BBVA SEGUROS A2052000420510-023-000",
            "19.02.25 362503V Spotify",
            "08.04.25 791406 OF USD 3,00",
            "19.06.25 241004F Spotify USD 2,90",
        ]

        # Test each line for proper reference detection
        import re

        pattern = r"([A-Z0-9*]+[*KQVF]?)\s+"

        for line in test_lines:
            # Extract the part after the date
            remaining_line = line[9:].strip()  # Skip "DD.MM.YY "
            match = re.match(pattern, remaining_line)
            assert match is not None, f"Pattern should match line: {line}"

            ref_number = match.group(1)
            # Verify the reference number is extracted correctly
            if "005302*" in line:
                assert ref_number == "005302*"
            elif "071512K" in line:
                assert ref_number == "071512K"
            elif "093709Q" in line:
                assert ref_number == "093709Q"
            elif "362503V" in line:
                assert ref_number == "362503V"
            elif "241004F" in line:
                assert ref_number == "241004F"
            elif "791406" in line:
                assert ref_number == "791406"

    def test_clean_ars_transaction_descriptions(self, parser):
        """Test that ARS transaction descriptions are cleaned up."""
        # Simulate PDF text with various reference patterns
        pdf_text = """
05.06.25 005302* ON FIT Cuota 06/06 32.990,00
18.01.25 001320* SANDRULI SRL 13.500,00
19.01.25 000001* AUBASA 960009587459301 1.599,79
30.01.25 071512K MERPAGO*THOMAS 10.200,00
01.02.25 891733K MERPAGO*LUCKY13 15.600,00
04.02.25 093709Q NETFLIX.COM 42785628363430465 7.199,00
13.02.25 994537* BBVA SEGUROS A2052000420510-023-000 11.862,41
19.02.25 362503V Spotify 3.299,00
08.04.25 791406 COMPRA ONLINE 1.500,00
"""

        transactions = parser._parse_transactions(pdf_text, PaymentMethod.BBVA_VISA)

        # Verify that descriptions are cleaned (no reference numbers)
        expected_descriptions = [
            "ON FIT Cuota 06/06",
            "SANDRULI SRL",
            "AUBASA 960009587459301",
            "MERPAGO*THOMAS",
            "MERPAGO*LUCKY13",
            "NETFLIX.COM 42785628363430465",
            "BBVA SEGUROS A2052000420510-023-000",
            "Spotify",
            "COMPRA ONLINE",
        ]

        assert len(transactions) == len(expected_descriptions)

        for i, (transaction, expected_desc) in enumerate(
            zip(transactions, expected_descriptions)
        ):
            assert transaction.description == expected_desc, (
                f"Transaction {i}: expected '{expected_desc}', got '{transaction.description}'"
            )
            assert transaction.currency == Currency.ARS
            assert transaction.payment_method == PaymentMethod.BBVA_VISA
            assert transaction.amount > 0

    def test_clean_usd_transaction_descriptions(self, parser):
        """Test that USD transaction descriptions are cleaned up."""
        pdf_text = """
08.04.25 791406 OF USD 3,00 3,00
19.06.25 241004F Spotify USD 2,90 2,90
"""

        transactions = parser._parse_transactions(pdf_text, PaymentMethod.BBVA_VISA)

        # Verify USD descriptions are cleaned
        expected_descriptions = [
            "OF USD 3,00",
            "Spotify USD 2,90",
        ]

        assert len(transactions) == len(expected_descriptions)

        for i, (transaction, expected_desc) in enumerate(
            zip(transactions, expected_descriptions)
        ):
            assert transaction.description == expected_desc, (
                f"USD Transaction {i}: expected '{expected_desc}', got '{transaction.description}'"
            )
            assert transaction.currency == Currency.USD
            assert transaction.payment_method == PaymentMethod.BBVA_VISA

    def test_non_reference_transactions_unchanged(self, parser):
        """Test that transactions without reference numbers are unchanged."""
        pdf_text = """
05.06.25 SU PAGO EN PESOS 50.000,00
06.06.25 IMPUESTO DE SELLOS 234,56
07.06.25 AJUSTE P/DESCNTO. EN COMERCIO 100,00
"""

        transactions = parser._parse_transactions(pdf_text, PaymentMethod.BBVA_VISA)

        expected_descriptions = [
            "SU PAGO EN PESOS",
            "IMPUESTO DE SELLOS",
            "AJUSTE P/DESCNTO. EN COMERCIO",
        ]

        assert len(transactions) == len(expected_descriptions)

        for i, (transaction, expected_desc) in enumerate(
            zip(transactions, expected_descriptions)
        ):
            assert transaction.description == expected_desc, (
                f"Non-ref Transaction {i}: expected '{expected_desc}', got '{transaction.description}'"
            )

    def test_macro_visa_descriptions_cleaned(self, parser):
        """Test that Macro Visa descriptions are also cleaned."""
        pdf_text = """
10.05.25 123456* MERCADOLIBRE COMPRA 45.600,00
11.05.25 789012K AMAZON PRIME VIDEO 999,00
"""

        transactions = parser._parse_transactions(pdf_text, PaymentMethod.MACRO_VISA)

        expected_descriptions = [
            "MERCADOLIBRE COMPRA",
            "AMAZON PRIME VIDEO",
        ]

        assert len(transactions) == len(expected_descriptions)

        for transaction, expected_desc in zip(transactions, expected_descriptions):
            assert transaction.description == expected_desc, (
                f"Macro transaction: expected '{expected_desc}', got '{transaction.description}'"
            )
            assert transaction.payment_method == PaymentMethod.MACRO_VISA

    def test_amount_parsing_preserved(self, parser):
        """Test that amount parsing functionality is preserved."""
        pdf_text = """
05.06.25 005302* ON FIT Cuota 06/06 32.990,00
18.01.25 001320* SANDRULI SRL 13.500,00
"""

        transactions = parser._parse_transactions(pdf_text, PaymentMethod.BBVA_VISA)

        assert len(transactions) == 2
        assert transactions[0].amount == Decimal("32990.00")
        assert transactions[1].amount == Decimal("13500.00")

    def test_date_parsing_preserved(self, parser):
        """Test that date parsing functionality is preserved."""
        pdf_text = """
05.06.25 005302* ON FIT Cuota 06/06 32.990,00
18.01.25 001320* SANDRULI SRL 13.500,00
"""

        transactions = parser._parse_transactions(pdf_text, PaymentMethod.BBVA_VISA)

        assert len(transactions) == 2
        assert transactions[0].date == date(2025, 6, 5)
        assert transactions[1].date == date(2025, 1, 18)

    def test_currency_detection_preserved(self, parser):
        """Test that currency detection is preserved."""
        pdf_text = """
05.06.25 005302* ON FIT Cuota 06/06 32.990,00
08.04.25 791406 OF USD 3,00 3,00
"""

        transactions = parser._parse_transactions(pdf_text, PaymentMethod.BBVA_VISA)

        assert len(transactions) == 2
        assert transactions[0].currency == Currency.ARS
        assert transactions[1].currency == Currency.USD

    def test_european_format_fallback_cleaned(self, parser):
        """Test that European format fallback descriptions are cleaned."""
        pdf_text = """
05.06.25 123456* SOME MERCHANT 1.234,56
"""

        transactions = parser._parse_transactions(pdf_text, PaymentMethod.BBVA_VISA)

        assert len(transactions) == 1
        assert transactions[0].description == "SOME MERCHANT"
        assert transactions[0].amount == Decimal("1234.56")

    def test_edge_cases_with_complex_descriptions(self, parser):
        """Test edge cases with complex merchant descriptions."""
        pdf_text = """
05.06.25 ABC123* MERCHANT NAME WITH NUMBERS 123456789 1.000,00
06.06.25 XYZ789K DESCRIPTION WITH SPECIAL-CHARS@SYMBOLS 2.500,50
"""

        transactions = parser._parse_transactions(pdf_text, PaymentMethod.BBVA_VISA)

        expected_descriptions = [
            "MERCHANT NAME WITH NUMBERS 123456789",
            "DESCRIPTION WITH SPECIAL-CHARS@SYMBOLS",
        ]

        assert len(transactions) == len(expected_descriptions)

        for transaction, expected_desc in zip(transactions, expected_descriptions):
            assert transaction.description == expected_desc, (
                f"Complex description: expected '{expected_desc}', got '{transaction.description}'"
            )

    def test_transaction_builder_integration(self, transaction_builder):
        """Test that TransactionBuilder works with cleaned descriptions."""
        # Test building transaction with clean description
        transaction = transaction_builder.build_from_pdf_line(
            date_str="05.06.25",
            description="ON FIT Cuota 06/06",  # Already cleaned
            amount_str="32.990,00",
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        assert transaction.description == "ON FIT Cuota 06/06"
        assert transaction.amount == Decimal("32990.00")
        assert transaction.currency == Currency.ARS
        assert transaction.payment_method == PaymentMethod.BBVA_VISA

    def test_regex_pattern_comprehensive(self):
        """Test the regex pattern comprehensively for all cases."""
        import re

        pattern = r"([A-Z0-9*]+[*KQVF]?)\s+"

        test_cases = [
            ("005302* ", "005302*"),
            ("001320* ", "001320*"),
            ("071512K ", "071512K"),
            ("093709Q ", "093709Q"),
            ("362503V ", "362503V"),
            ("241004F ", "241004F"),
            ("791406 ", "791406"),
            ("ABC123* ", "ABC123*"),
            ("XYZ789K ", "XYZ789K"),
            ("123Q ", "123Q"),
            ("456V ", "456V"),
            ("789F ", "789F"),
        ]

        for test_input, expected_ref in test_cases:
            match = re.match(pattern, test_input)
            assert match is not None, f"Pattern should match: {test_input}"
            assert match.group(1) == expected_ref, (
                f"Expected {expected_ref}, got {match.group(1)}"
            )
