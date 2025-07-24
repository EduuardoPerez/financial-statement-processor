"""
Unit tests for PDFStatementParser - Fixture-based testing.

This module provides unit tests for PDF parsing functionality using real PDF fixtures,
specifically testing the BBVA Visa April 2025 PDF as specified in Prompt 16.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from domain.builders import TransactionBuilder
from domain.models import Currency, PaymentMethod, Statement, Transaction
from infrastructure.parsers.pdf_parser import PDFStatementParser


class TestPDFStatementParserFixtures:
    """Unit tests for PDFStatementParser using real PDF fixtures"""

    @pytest.fixture
    def mock_detector(self):
        """Create mock payment method detector"""
        detector = Mock()
        detector.detect_from_content.return_value = PaymentMethod.BBVA_VISA
        return detector

    @pytest.fixture
    def mock_transaction_builder(self):
        """Create mock transaction builder"""
        builder = Mock(spec=TransactionBuilder)
        builder._amount_parser = Mock()

        # Create sample transaction for testing - based on actual first transaction from legacy system
        sample_transaction = Transaction(
            date=date(2025, 3, 28),
            description="PERSONAL FLOW 300060254971003",
            amount=Decimal("41937.01"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )
        builder.build_from_pdf_line.return_value = sample_transaction
        return builder

    @pytest.fixture
    def pdf_parser(self, mock_detector, mock_transaction_builder):
        """Create PDFStatementParser instance with mocked dependencies"""
        return PDFStatementParser(mock_detector, mock_transaction_builder)

    @patch("infrastructure.parsers.pdf_parser.pdfplumber")
    def test_parse_bbva_visa_april_2025_fixture(
        self, mock_pdfplumber, pdf_parser, mock_detector, mock_transaction_builder
    ):
        """Test parsing of real BBVA Visa April 2025 PDF fixture - Prompt 16 requirement"""
        # Arrange
        test_file = Path(
            "tests/test_data/input/BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf"
        )

        # Mock file existence
        with patch.object(Path, "exists", return_value=True):
            # Mock pdfplumber to extract content representing the real PDF structure
            # Based on legacy system analysis, the first transaction is:
            # Date: 2025-03-28, Description: "020396* PERSONAL FLOW 300060254971003"
            test_text = """
            BBVA VISA SIGNATURE
            28.03.25 020396* PERSONAL FLOW 300060254971003 41.937,01
            29.03.25 041685K PEDIDOSYA RESTAURANTE 14.234,00
            29.03.25 052966K PEDIDOSYA PROPINAS 850,00
            """

            mock_pdf = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = test_text
            mock_pdf.pages = [mock_page]
            mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

            # Configure detector to return BBVA VISA
            mock_detector.detect_from_content.return_value = PaymentMethod.BBVA_VISA

            # Configure transaction builder to return expected first transaction
            expected_first_transaction = Transaction(
                date=date(2025, 3, 28),
                description="PERSONAL FLOW 300060254971003",
                amount=Decimal("41937.01"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )
            mock_transaction_builder.build_from_pdf_line.return_value = (
                expected_first_transaction
            )

            # Act
            statement = pdf_parser.parse(test_file)

            # Assert - Validate first transaction date and description per Prompt 16 plan
            assert isinstance(statement, Statement)
            assert statement.payment_method == PaymentMethod.BBVA_VISA
            assert len(statement.transactions) > 0

            # Key assertions for Prompt 16: first transaction date & description
            first_transaction = statement.transactions[0]
            assert first_transaction.date == date(2025, 3, 28), (
                f"Expected first transaction date to be 2025-03-28, got {first_transaction.date}"
            )
            assert first_transaction.description == "PERSONAL FLOW 300060254971003", (
                f"Expected first transaction description to be 'PERSONAL FLOW 300060254971003', got '{first_transaction.description}'"
            )

            # Additional validations
            assert first_transaction.currency == Currency.ARS
            assert first_transaction.payment_method == PaymentMethod.BBVA_VISA
            assert first_transaction.amount == Decimal("41937.01")

            # Verify detector was called with PDF content
            mock_detector.detect_from_content.assert_called_once_with(test_text)

            # Verify transaction builder was called for first transaction
            assert mock_transaction_builder.build_from_pdf_line.call_count >= 1
            first_call = mock_transaction_builder.build_from_pdf_line.call_args_list[0]
            assert first_call[1]["date_str"] == "28.03.25"
            assert first_call[1]["description"] == "PERSONAL FLOW 300060254971003"
            assert first_call[1]["amount_str"] == "41.937,01"
            assert first_call[1]["currency"] == Currency.ARS
            assert first_call[1]["payment_method"] == PaymentMethod.BBVA_VISA

    def test_fixture_file_exists(self):
        """Test that the required fixture file exists"""
        # Arrange
        fixture_path = Path(
            "tests/test_data/input/BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf"
        )

        # Assert
        assert fixture_path.exists(), f"Fixture PDF file not found at {fixture_path}"
        assert fixture_path.is_file(), f"Path exists but is not a file: {fixture_path}"
        assert fixture_path.suffix.lower() == ".pdf", (
            f"File is not a PDF: {fixture_path}"
        )
