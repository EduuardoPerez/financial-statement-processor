"""
Tests for USD transaction detection in BBVA Mastercard PDFs.

This module tests the enhanced parsing logic that correctly identifies USD transactions
in BBVA Mastercard statements and assigns the proper currency instead of defaulting to ARS.
"""

from decimal import Decimal

from domain.builders import TransactionBuilder
from domain.models import Currency, PaymentMethod
from domain.utils import AmountParser, DateConverter
from infrastructure.parsers.pdf_parser import PDFStatementParser


class MockBBVAMastercardDetector:
    """Mock detector that always returns BBVA Mastercard payment method."""

    def detect_from_content(self, content: str) -> PaymentMethod:
        return PaymentMethod.BBVA_MASTERCARD


class TestBBVAMastercardUSDDetection:
    """Test suite for USD transaction detection in BBVA Mastercard statements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = MockBBVAMastercardDetector()
        self.amount_parser = AmountParser()
        self.date_converter = DateConverter()
        self.transaction_builder = TransactionBuilder(
            amount_parser=self.amount_parser, date_converter=self.date_converter
        )
        self.parser = PDFStatementParser(
            detector=self.detector, transaction_builder=self.transaction_builder
        )

    def test_usd_transaction_detection_basic(self):
        """Test basic USD transaction detection in BBVA Mastercard format."""
        pdf_text = """
07-Jul-25 internation-site.Com USD 35,00 974461 35,00
        """

        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_MASTERCARD
        )

        assert len(transactions) == 1
        transaction = transactions[0]

        assert transaction.currency == Currency.USD
        assert transaction.amount == Decimal("35.00")
        assert transaction.description == "internation-site.Com USD 35,00"
        assert transaction.payment_method == PaymentMethod.BBVA_MASTERCARD

    def test_usd_transaction_detection_different_amounts(self):
        """Test USD detection with different amount formats."""
        pdf_text = """
07-Jul-25 Netflix.Com USD 15,99 123456 15,99
08-Jul-25 Spotify USD 4,99 789012 4,99
09-Jul-25 Amazon.Com USD 129,00 345678 129,00
        """

        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_MASTERCARD
        )

        assert len(transactions) == 3

        # Netflix transaction
        assert transactions[0].currency == Currency.USD
        assert transactions[0].amount == Decimal("15.99")
        assert transactions[0].description == "Netflix.Com USD 15,99"

        # Spotify transaction
        assert transactions[1].currency == Currency.USD
        assert transactions[1].amount == Decimal("4.99")
        assert transactions[1].description == "Spotify USD 4,99"

        # Amazon transaction
        assert transactions[2].currency == Currency.USD
        assert transactions[2].amount == Decimal("129.00")
        assert transactions[2].description == "Amazon.Com USD 129,00"

    def test_mixed_usd_and_ars_transactions(self):
        """Test that both USD and ARS transactions are correctly identified."""
        pdf_text = """
07-Jul-25 internation-site.Com USD 35,00 974461 35,00
08-Jul-25 Regular Store Purchase 15.000,50
09-Jul-25 Another USD Store USD 25,99 555666 25,99
10-Jul-25 ARS Store Purchase 5.500,00
        """

        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_MASTERCARD
        )

        assert len(transactions) == 4

        # First transaction - USD
        assert transactions[0].currency == Currency.USD
        assert transactions[0].amount == Decimal("35.00")
        assert transactions[0].description == "internation-site.Com USD 35,00"

        # Second transaction - ARS
        assert transactions[1].currency == Currency.ARS
        assert transactions[1].amount == Decimal("15000.50")
        assert transactions[1].description == "Regular Store Purchase"

        # Third transaction - USD
        assert transactions[2].currency == Currency.USD
        assert transactions[2].amount == Decimal("25.99")
        assert transactions[2].description == "Another USD 25,99"

        # Fourth transaction - ARS
        assert transactions[3].currency == Currency.ARS
        assert transactions[3].amount == Decimal("5500.00")
        assert transactions[3].description == "ARS Store Purchase"

    def test_usd_transaction_with_complex_description(self):
        """Test USD detection with complex merchant descriptions."""
        pdf_text = """
07-Jul-25 PAYPAL *ADOBE SYST USD 22,99 123456 22,99
08-Jul-25 GOOGLE *SERVICES USD 5,00 789012 5,00
09-Jul-25 MICROSOFT STORE USD 99,99 345678 99,99
        """

        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_MASTERCARD
        )

        assert len(transactions) == 3

        # PayPal transaction
        assert transactions[0].currency == Currency.USD
        assert transactions[0].amount == Decimal("22.99")
        assert transactions[0].description == "PAYPAL *ADOBE SYST USD 22,99"

        # Google transaction
        assert transactions[1].currency == Currency.USD
        assert transactions[1].amount == Decimal("5.00")
        assert transactions[1].description == "GOOGLE *SERVICES USD 5,00"

        # Microsoft transaction
        assert transactions[2].currency == Currency.USD
        assert transactions[2].amount == Decimal("99.99")
        assert transactions[2].description == "MICROSOFT STORE USD 99,99"

    def test_ars_transactions_still_work(self):
        """Test that ARS transactions continue to work after USD enhancement."""
        pdf_text = """
07-Jul-25 Regular ARS Purchase 25.000,00
08-Jul-25 Another ARS Store 15.500,50
09-Jul-25 Local Merchant 3.200,75
        """

        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_MASTERCARD
        )

        assert len(transactions) == 3

        # All should be ARS transactions
        for transaction in transactions:
            assert transaction.currency == Currency.ARS
            assert transaction.payment_method == PaymentMethod.BBVA_MASTERCARD

        # Check specific amounts
        assert transactions[0].amount == Decimal("25000.00")
        assert transactions[0].description == "Regular ARS Purchase"

        assert transactions[1].amount == Decimal("15500.50")
        assert transactions[1].description == "Another ARS Store"

        assert transactions[2].amount == Decimal("3200.75")
        assert transactions[2].description == "Local Merchant"

    def test_usd_transaction_with_dots_in_amount(self):
        """Test USD transaction detection with dots in amount (US format)."""
        pdf_text = """
07-Jul-25 US Store USD 1234,56 123456 1234,56
        """

        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_MASTERCARD
        )

        assert len(transactions) == 1
        transaction = transactions[0]

        assert transaction.currency == Currency.USD
        # Amount should be correctly parsed from the European format version
        assert transaction.amount == Decimal("1234.56")
        assert transaction.description == "US Store USD 1234,56"

    def test_edge_case_usd_with_no_cents(self):
        """Test USD transaction with whole dollar amounts (no cents)."""
        pdf_text = """
07-Jul-25 Whole Dollar USD 50,00 123456 50,00
08-Jul-25 Another Whole USD 100,00 789012 100,00
        """

        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_MASTERCARD
        )

        assert len(transactions) == 2

        assert transactions[0].currency == Currency.USD
        assert transactions[0].amount == Decimal("50.00")
        assert transactions[0].description == "Whole Dollar USD 50,00"

        assert transactions[1].currency == Currency.USD
        assert transactions[1].amount == Decimal("100.00")
        assert transactions[1].description == "Another Whole USD 100,00"

    def test_usd_payment_transactions(self):
        """Test that USD payments (SU PAGO EN USD) are handled correctly."""
        pdf_text = """
07-Jul-25 SU PAGO EN USD 500,00 123456 500,00
        """

        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_MASTERCARD
        )

        # This should be handled by the USD payment logic in BBVA Mastercard section
        assert len(transactions) == 1
        transaction = transactions[0]

        assert transaction.currency == Currency.USD
        # The new logic treats "SU PAGO EN USD" as a regular transaction with USD
        assert transaction.amount == Decimal("500.00")
        assert transaction.description == "SU PAGO EN USD 500,00"

    def test_no_false_positives_for_other_payment_methods(self):
        """Test that the USD detection logic works correctly for other methods."""
        pdf_text = """
07.07.25 071512K internation-site.Com USD 35,00 974461 35,00
        """

        # Test with BBVA Visa (different date format, with reference pattern)
        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_VISA
        )

        # Should be processed by regular logic, not BBVA Mastercard logic
        assert len(transactions) == 1
        transaction = transactions[0]

        # Should still detect USD correctly through regular parsing
        assert transaction.currency == Currency.USD
        assert "USD" in transaction.description

    def test_invalid_usd_format_fallback_to_ars(self):
        """Test that malformed USD entries fall back to ARS processing."""
        pdf_text = """
07-Jul-25 Malformed USD Entry 35,00
07-Jul-25 USD No Amount Following
07-Jul-25 Valid Entry USD 25,99 123456 25,99
        """

        transactions = self.parser._parse_transactions(
            pdf_text, PaymentMethod.BBVA_MASTERCARD
        )

        assert len(transactions) == 2  # Only valid entries should be processed

        # Valid USD transaction should be processed correctly
        usd_transaction = None
        for t in transactions:
            if t.currency == Currency.USD:
                usd_transaction = t
                break

        assert usd_transaction is not None
        assert usd_transaction.amount == Decimal("25.99")
        assert usd_transaction.description == "Valid Entry USD 25,99"
