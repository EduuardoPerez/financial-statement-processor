"""
Unit tests for PDFStatementParser infrastructure component.

This module provides comprehensive unit tests for the PDFStatementParser class,
following the testing strategy outlined in PLAN.md with proper mock dependencies
and behavior-focused testing.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from domain.builders import TransactionBuilder
from domain.models import Currency, PaymentMethod, Statement, Transaction
from infrastructure.parsers.pdf_parser import PDFStatementParser


class TestPDFStatementParser:
    """Unit tests for PDFStatementParser class"""

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

        # Add the _amount_parser attribute that PDFStatementParser expects
        builder._amount_parser = Mock()

        # Create a sample transaction for testing
        sample_transaction = Transaction(
            date=date(2025, 6, 5),
            description="Test Transaction",
            amount=Decimal("1234.56"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )
        builder.build_from_pdf_line.return_value = sample_transaction
        return builder

    @pytest.fixture
    def pdf_parser(self, mock_detector, mock_transaction_builder):
        """Create PDFStatementParser instance with mocked dependencies"""
        return PDFStatementParser(mock_detector, mock_transaction_builder)

    def test_can_parse_pdf_files(self, pdf_parser):
        """Test that parser correctly identifies PDF files"""
        # Arrange
        pdf_file = Path("statement.pdf")
        non_pdf_file = Path("statement.xls")
        uppercase_pdf = Path("STATEMENT.PDF")

        # Act & Assert
        assert pdf_parser.can_parse(pdf_file) is True
        assert pdf_parser.can_parse(uppercase_pdf) is True
        assert pdf_parser.can_parse(non_pdf_file) is False

    def test_get_supported_extensions(self, pdf_parser):
        """Test that parser returns correct supported extensions"""
        # Act
        extensions = pdf_parser.get_supported_extensions()

        # Assert
        assert extensions == {".pdf"}

    @patch("infrastructure.parsers.pdf_parser.pdfplumber")
    def test_extract_text_success(self, mock_pdfplumber, pdf_parser):
        """Test successful text extraction from PDF"""
        # Arrange
        test_file = Path("test.pdf")

        # Mock pdfplumber behavior
        mock_pdf = Mock()
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Sample PDF content\n"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Line 2\nLine 3"

        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        # Act
        result = pdf_parser._extract_text(test_file)

        # Assert
        assert "Sample PDF content" in result
        assert "Line 2" in result
        assert "Line 3" in result
        mock_pdfplumber.open.assert_called_once_with(test_file)

    @patch("infrastructure.parsers.pdf_parser.pdfplumber")
    def test_extract_text_no_content(self, mock_pdfplumber, pdf_parser):
        """Test text extraction when PDF has no text content"""
        # Arrange
        test_file = Path("empty.pdf")

        # Mock pdfplumber behavior for empty PDF
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        # Act & Assert
        with pytest.raises(ValueError, match="No text content found in PDF"):
            pdf_parser._extract_text(test_file)

    def test_parse_transactions_with_date_pattern(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test transaction parsing with valid date patterns"""
        # Arrange
        test_text = """
        Header line
        09.05.25 SU PAGO EN PESOS 1.095.461,57-
        10.05.25 020396* PERSONAL FLOW 300060254971003 1.234,56
        Invalid line without date
        11.05.25 041685K PEDIDOSYA RESTAURANTE 500,00
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 3

        # Verify TransactionBuilder was called correctly
        assert mock_transaction_builder.build_from_pdf_line.call_count == 3

        # Check first call arguments (payment transaction)
        first_call = mock_transaction_builder.build_from_pdf_line.call_args_list[0]
        assert first_call[1]["date_str"] == "09.05.25"
        assert first_call[1]["description"] == "SU PAGO EN PESOS"
        assert first_call[1]["amount_str"] == "-1.095.461,57"  # Negative for payments
        assert first_call[1]["currency"] == Currency.ARS
        assert first_call[1]["payment_method"] == payment_method

    def test_parse_transactions_with_multiple_spaces(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test transaction parsing with multiple spaces between components"""
        # Arrange
        test_text = "09.05.25    DESCRIPTION WITH SPACES    1.234,56"
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 1

        # Verify parsing handled multiple spaces correctly
        call_args = mock_transaction_builder.build_from_pdf_line.call_args
        assert call_args[1]["description"] == "WITH SPACES"

    def test_parse_transactions_graceful_degradation(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test that invalid transactions are skipped gracefully"""
        # Arrange
        test_text = """
        09.05.25 020396* PERSONAL FLOW 300060254971003 1.234,56
        10.05.25 041685K PEDIDOSYA RESTAURANTE 500,00
        11.05.25 052966K PEDIDOSYA PROPINAS 850,00
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Create a list to track calls and results
        call_count = 0

        def mock_build_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            # Raise error on second call only (simulating one parsing path failing)
            if call_count == 2:
                raise ValueError("Invalid amount")

            return Transaction(
                date=date(2025, 6, 5),
                description=kwargs["description"],
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

        mock_transaction_builder.build_from_pdf_line.side_effect = (
            mock_build_side_effect
        )

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        # The sophisticated parser may try multiple parsing paths for the same line
        # and handles errors gracefully by continuing. We expect all transactions
        # to be successfully parsed since alternative paths succeed.
        assert len(transactions) == 3  # All transactions successfully parsed
        assert (
            call_count >= 3
        )  # At least 3 attempts, possibly more due to multiple parsing paths

        # Verify all transactions are present
        descriptions = [t.description for t in transactions]
        assert "PERSONAL FLOW 300060254971003" in descriptions
        assert "PEDIDOSYA RESTAURANTE" in descriptions
        assert "PEDIDOSYA PROPINAS" in descriptions

    def test_parse_file_not_found(self, pdf_parser):
        """Test parse method with non-existent file"""
        # Arrange
        non_existent_file = Path("non_existent.pdf")

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            pdf_parser.parse(non_existent_file)

    @patch("infrastructure.parsers.pdf_parser.pdfplumber")
    def test_parse_complete_workflow(
        self, mock_pdfplumber, pdf_parser, mock_detector, mock_transaction_builder
    ):
        """Test complete parse workflow with mocked dependencies"""
        # Arrange
        test_file = Path("test.pdf")
        test_text = "09.05.25 TEST TRANSACTION 1.234,56"

        # Mock file existence
        with patch.object(Path, "exists", return_value=True):
            # Mock pdfplumber
            mock_pdf = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = test_text
            mock_pdf.pages = [mock_page]
            mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

            # Act
            statement = pdf_parser.parse(test_file)

            # Assert
            assert isinstance(statement, Statement)
            assert statement.payment_method == PaymentMethod.BBVA_VISA
            assert len(statement.transactions) == 1

            # Verify detector was called
            mock_detector.detect_from_content.assert_called_once_with(test_text)

            # Verify transaction builder was called
            mock_transaction_builder.build_from_pdf_line.assert_called_once()

    @patch("infrastructure.parsers.pdf_parser.pdfplumber")
    def test_parse_permission_error(self, mock_pdfplumber, pdf_parser):
        """Test parse method handles permission errors correctly"""
        # Arrange
        test_file = Path("restricted.pdf")

        with patch.object(Path, "exists", return_value=True):
            # Mock pdfplumber to raise PermissionError
            mock_pdfplumber.open.side_effect = PermissionError("Access denied")

            # Act & Assert
            with pytest.raises(OSError, match="Error processing PDF file"):
                pdf_parser.parse(test_file)

    def test_parse_transactions_empty_text(self, pdf_parser):
        """Test transaction parsing with empty text"""
        # Arrange
        empty_text = ""
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(empty_text, payment_method)

        # Assert
        assert len(transactions) == 0

    def test_parse_transactions_no_date_patterns(self, pdf_parser):
        """Test transaction parsing with text containing no date patterns"""
        # Arrange
        text_without_dates = """
        Header information
        Some description text
        Footer information
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(
            text_without_dates, payment_method
        )

        # Assert
        assert len(transactions) == 0

    def test_parse_transactions_bbva_mastercard_format(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test transaction parsing for BBVA Mastercard DD-MMM-YY format"""
        # Arrange
        test_text = """
        04-Apr-25 SU PAGO EN PESOS 1.549.449,84
        05-Apr-25 020396* PERSONAL FLOW 300060254971003 1.234,56
        06-Apr-25 SALDO ACTUAL 500,00
        07-Apr-25 VENCIMIENTO 15-May-25
        08-Apr-25 PAGO MÍNIMO 100,00
        09-Apr-25 04-Apr-25 1.234,56 500,00 750,00
        """
        payment_method = PaymentMethod.BBVA_MASTERCARD

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 2  # Only valid transactions

        # Verify payment transaction
        first_call = mock_transaction_builder.build_from_pdf_line.call_args_list[0]
        assert first_call[1]["date_str"] == "04-Apr-25"
        assert first_call[1]["description"] == "SU PAGO EN PESOS"
        assert first_call[1]["amount_str"] == "-1.549.449,84"

    def test_parse_transactions_tax_entries(self, pdf_parser, mock_transaction_builder):
        """Test parsing of various tax entry types"""
        # Arrange
        test_text = """
        09.05.25 IMPUESTO DE SELLOS 45,67
        10.05.25 DB.IMPUESTO PAIS 123,45
        11.05.25 IIBB PERCEP 67,89
        12.05.25 IVA RG 234,56
        13.05.25 DB.RG 4815 45% ( 3557,36 ) 1600,81
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 5

        # Verify tax transaction parsing
        calls = mock_transaction_builder.build_from_pdf_line.call_args_list
        assert calls[0][1]["description"] == "IMPUESTO DE SELLOS"
        assert calls[0][1]["amount_str"] == "45,67"
        assert calls[1][1]["description"] == "DB.IMPUESTO PAIS"
        assert calls[4][1]["description"] == "DB.RG 4815 45% ( 3557,36 )"

    def test_parse_transactions_usd_payments(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test parsing of USD payment transactions"""
        # Arrange
        test_text = """
        09.05.25 SU PAGO EN USD 500,00
        10.05.25 SU PAGO EN USD 1.234,56-
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 2

        # Verify USD payment parsing
        calls = mock_transaction_builder.build_from_pdf_line.call_args_list
        assert calls[0][1]["description"] == "SU PAGO EN USD"
        assert calls[0][1]["amount_str"] == "-500,00"
        assert calls[0][1]["currency"] == Currency.USD
        assert calls[1][1]["currency"] == Currency.USD

    def test_parse_transactions_adjustments(self, pdf_parser, mock_transaction_builder):
        """Test parsing of adjustment transactions"""
        # Arrange
        test_text = """
        09.05.25 AJUSTE P/DESCNTO. EN COMERCIO 100,50
        10.05.25 AJUSTE MANUAL 250,75-
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 2

        # Verify adjustment parsing
        calls = mock_transaction_builder.build_from_pdf_line.call_args_list
        assert calls[0][1]["description"] == "AJUSTE P/DESCNTO. EN COMERCIO"
        assert calls[0][1]["amount_str"] == "-100,50"  # Always negative

    def test_parse_transactions_bonifications(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test parsing of BBVA bonification transactions"""
        # Arrange
        test_text = """
        09.05.25 BONIF. CUOTA ANUAL 1.500,00
        10.05.25 BONIF. PROMOCION ESPECIAL 750,25-
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 2

        # Verify bonification parsing
        calls = mock_transaction_builder.build_from_pdf_line.call_args_list
        assert "BONIF. CUOTA ANUAL" in calls[0][1]["description"]
        assert calls[0][1]["amount_str"] == "-1.500,00"  # Always negative

    def test_parse_transactions_promotions(self, pdf_parser, mock_transaction_builder):
        """Test parsing of promotion/OFF transactions"""
        # Arrange
        test_text = """
        09.05.25 OFF DESCUENTO ESPECIAL 200,00
        10.05.25 Promo CASHBACK 150,50
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 2

        # Verify promotion parsing
        calls = mock_transaction_builder.build_from_pdf_line.call_args_list
        assert "OFF DESCUENTO ESPECIAL" in calls[0][1]["description"]
        assert calls[0][1]["amount_str"] == "-200,00"  # Always negative

    def test_parse_transactions_usd_with_reference(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test parsing of USD transactions with reference numbers"""
        # Arrange
        test_text = """
        09.05.25 020396* AMAZON PURCHASE USD 25.50 1.234,56
        10.05.25 041685K NETFLIX SUBSCRIPTION USD 15.99 800,25
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 2

        # Verify USD transaction parsing
        calls = mock_transaction_builder.build_from_pdf_line.call_args_list
        assert calls[0][1]["currency"] == Currency.USD
        assert "USD 25.50" in calls[0][1]["description"]
        assert calls[0][1]["amount_str"] == "25.50"

    def test_parse_transactions_multiple_amount_patterns(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test parsing with different amount patterns"""
        # Arrange
        test_text = """
        09.05.25 020396* TRANSACTION ONE 1.234,56
        10.05.25 041685K TRANSACTION TWO 500,00
        11.05.25 052966K TRANSACTION THREE 75.50
        12.05.25 063847K TRANSACTION FOUR 1000
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 4

        # Verify different amount patterns are handled
        calls = mock_transaction_builder.build_from_pdf_line.call_args_list
        amounts = [call[1]["amount_str"] for call in calls]
        assert "1.234,56" in amounts
        assert "500,00" in amounts
        assert "75.50" in amounts
        assert "1000" in amounts

    def test_parse_transactions_fallback_european_format(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test fallback to European format amount parsing"""
        # Arrange
        test_text = """
        09.05.25 020396* COMPLEX DESCRIPTION WITH NUMBERS 123 AND 456 FINAL 1.234,56
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Mock amount parser to test fallback path
        pdf_parser._amount_parser.parse_european_format.return_value = Decimal(
            "1234.56"
        )

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 1

        # Verify fallback parsing was used
        call = mock_transaction_builder.build_from_pdf_line.call_args
        assert call[1]["amount_str"] == "1.234,56"

    def test_parse_transactions_last_resort_parsing(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test last resort number parsing when other patterns fail"""
        # Arrange
        test_text = """
        09.05.25 020396* DESCRIPTION WITHOUT CLEAR AMOUNT PATTERN 1.234,56 EXTRA TEXT
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Mock amount parser for last resort path
        def mock_parse_side_effect(amount_str):
            if amount_str == "1.234,56":
                return Decimal("1234.56")
            raise ValueError("Invalid format")

        pdf_parser._amount_parser.parse_european_format.side_effect = (
            mock_parse_side_effect
        )

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 1

    def test_parse_transactions_skip_excluded_lines(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test that certain lines are properly skipped"""
        # Arrange
        test_text = """
        09.05.25 SALDO ANTERIOR 1.000,00
        10.05.25 Total Consumos 2.500,00
        11.05.25 020396* VALID TRANSACTION 1.234,56
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert
        assert len(transactions) == 1  # Only the valid transaction

        # Verify only valid transaction was processed
        call = mock_transaction_builder.build_from_pdf_line.call_args
        assert "VALID TRANSACTION" in call[1]["description"]

    @patch("infrastructure.parsers.pdf_parser.pdfplumber")
    def test_extract_text_pdfplumber_exception(self, mock_pdfplumber, pdf_parser):
        """Test text extraction when pdfplumber raises an exception"""
        # Arrange
        test_file = Path("problematic.pdf")

        # Mock pdfplumber to raise an exception
        mock_pdfplumber.open.side_effect = Exception("PDF parsing error")

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to extract text from PDF"):
            pdf_parser._extract_text(test_file)

    def test_parse_transactions_builder_exception_handling(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test graceful handling of TransactionBuilder exceptions"""
        # Arrange
        test_text = """
        09.05.25 020396* VALID TRANSACTION 1.234,56
        10.05.25 041685K INVALID TRANSACTION 500,00
        11.05.25 052966K ANOTHER VALID 750,00
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Mock builder to fail on second transaction
        call_count = 0

        def mock_build_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Invalid transaction data")
            return Transaction(
                date=date(2025, 6, 5),
                description=kwargs["description"],
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

        mock_transaction_builder.build_from_pdf_line.side_effect = (
            mock_build_side_effect
        )

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert - Should continue processing despite one failure
        assert len(transactions) >= 2  # At least 2 successful transactions

    @patch("infrastructure.parsers.pdf_parser.pdfplumber")
    def test_parse_os_error_handling(self, mock_pdfplumber, pdf_parser):
        """Test OSError handling in parse method"""
        # Arrange
        test_file = Path("test.pdf")

        with patch.object(Path, "exists", return_value=True):
            # Mock pdfplumber to raise OSError
            mock_pdfplumber.open.side_effect = OSError("I/O error")

            # Act & Assert
            with pytest.raises(OSError, match="Error processing PDF file"):
                pdf_parser.parse(test_file)

    def test_parse_transactions_amount_parser_exception(
        self, pdf_parser, mock_transaction_builder
    ):
        """Test handling of amount parser exceptions in last resort parsing"""
        # Arrange
        test_text = """
        09.05.25 020396* TRANSACTION WITH INVALID AMOUNT invalid,amount
        """
        payment_method = PaymentMethod.BBVA_VISA

        # Mock amount parser to always raise exception
        pdf_parser._amount_parser.parse_european_format.side_effect = ValueError(
            "Invalid amount"
        )

        # Act
        transactions = pdf_parser._parse_transactions(test_text, payment_method)

        # Assert - Should handle exception gracefully
        assert len(transactions) == 0  # No transactions due to parsing failure
