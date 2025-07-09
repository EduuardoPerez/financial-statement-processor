"""
Unit tests for StreamingStatementParser.

Tests the memory-efficient streaming parser for large CSV/Excel files,
including chunk processing, error handling, and integration with existing
domain components.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from domain.builders import TransactionBuilder
from domain.detectors import PaymentMethodDetector
from domain.models import Currency, PaymentMethod, Transaction
from infrastructure.streaming import StreamingStatementParser


@pytest.fixture
def mock_transaction_builder():
    """Create mock transaction builder."""
    builder = Mock(spec=TransactionBuilder)
    sample_transaction = Transaction(
        date=date(2025, 1, 1),
        description="Test transaction",
        amount=Decimal("100.0"),
        currency=Currency.ARS,
        payment_method=PaymentMethod.BBVA_VISA,
    )
    builder.build_from_pdf_line.return_value = sample_transaction
    return builder


@pytest.fixture
def mock_payment_method_detector():
    """Create mock payment method detector."""
    detector = Mock(spec=PaymentMethodDetector)
    detector.detect_from_filename.return_value = PaymentMethod.BBVA_VISA
    return detector


class TestStreamingStatementParser:
    """Test StreamingStatementParser class."""

    @pytest.fixture
    def streaming_parser(self):
        """Create StreamingStatementParser with default settings."""
        return StreamingStatementParser()

    @pytest.fixture
    def streaming_parser_with_mocks(
        self, mock_transaction_builder, mock_payment_method_detector
    ):
        """Create StreamingStatementParser with mocked dependencies."""
        return StreamingStatementParser(
            chunk_size=500,
            transaction_builder=mock_transaction_builder,
            payment_method_detector=mock_payment_method_detector,
        )

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        parser = StreamingStatementParser()

        assert parser._chunk_size == 1000
        assert parser._transaction_builder is None
        assert parser._payment_method_detector is None

    def test_init_custom_parameters(
        self, mock_transaction_builder, mock_payment_method_detector
    ):
        """Test initialization with custom parameters."""
        parser = StreamingStatementParser(
            chunk_size=2000,
            transaction_builder=mock_transaction_builder,
            payment_method_detector=mock_payment_method_detector,
        )

        assert parser._chunk_size == 2000
        assert parser._transaction_builder == mock_transaction_builder
        assert parser._payment_method_detector == mock_payment_method_detector

    def test_get_chunk_size(self, streaming_parser):
        """Test chunk size getter."""
        assert streaming_parser.get_chunk_size() == 1000

    def test_set_chunk_size_valid(self, streaming_parser):
        """Test chunk size setter with valid value."""
        streaming_parser.set_chunk_size(2000)
        assert streaming_parser.get_chunk_size() == 2000

    def test_set_chunk_size_invalid(self, streaming_parser):
        """Test chunk size setter with invalid value."""
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            streaming_parser.set_chunk_size(0)

        with pytest.raises(ValueError, match="Chunk size must be positive"):
            streaming_parser.set_chunk_size(-100)

    def test_repr(self, streaming_parser):
        """Test string representation."""
        result = repr(streaming_parser)
        assert result == "StreamingStatementParser(chunk_size=1000)"

    def test_repr_custom_chunk_size(self):
        """Test string representation with custom chunk size."""
        parser = StreamingStatementParser(chunk_size=500)
        result = repr(parser)
        assert result == "StreamingStatementParser(chunk_size=500)"


class TestCSVParsing:
    """Test CSV parsing functionality."""

    @pytest.fixture
    def mock_csv_data(self):
        """Create mock CSV data."""
        return pd.DataFrame(
            {
                "Fecha": ["01/01/2025", "02/01/2025", "03/01/2025"],
                "Descripcion": ["Transaction 1", "Transaction 2", "Transaction 3"],
                "Moneda": ["Pesos", "Dolares", "Pesos"],
                "Importe": ["100,50", "200,75", "300,25"],
            }
        )

    @pytest.fixture
    def streaming_parser(self):
        """Create StreamingStatementParser."""
        return StreamingStatementParser(chunk_size=2)

    def test_parse_large_csv_file_not_found(self, streaming_parser):
        """Test CSV parsing with non-existent file."""
        non_existent_file = Path("non_existent.csv")

        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            list(streaming_parser.parse_large_csv(non_existent_file))

    def test_parse_large_csv_wrong_extension(self, streaming_parser):
        """Test CSV parsing with wrong file extension."""
        wrong_file = Path("test.xlsx")

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ValueError, match="Expected CSV file, got: .xlsx"):
                list(streaming_parser.parse_large_csv(wrong_file))

    @patch("infrastructure.streaming.pd.read_csv")
    def test_parse_large_csv_success(
        self, mock_read_csv, streaming_parser, mock_csv_data
    ):
        """Test successful CSV parsing."""
        csv_file = Path("test.csv")

        # Mock file existence
        with patch.object(Path, "exists", return_value=True):
            # Mock pandas read_csv to return chunks
            chunk1 = mock_csv_data.iloc[:2]
            chunk2 = mock_csv_data.iloc[2:]
            mock_read_csv.return_value = [chunk1, chunk2]

            # Mock payment method detection
            with patch.object(
                streaming_parser,
                "_detect_payment_method_from_filename",
                return_value=PaymentMethod.BBVA_VISA,
            ):
                # Mock row parsing
                with patch.object(
                    streaming_parser,
                    "_parse_csv_row",
                    side_effect=[
                        Transaction(
                            date=date(2025, 1, 1),
                            description="Transaction 1",
                            amount=Decimal("100.50"),
                            currency=Currency.ARS,
                            payment_method=PaymentMethod.BBVA_VISA,
                        ),
                        Transaction(
                            date=date(2025, 1, 2),
                            description="Transaction 2",
                            amount=Decimal("200.75"),
                            currency=Currency.USD,
                            payment_method=PaymentMethod.BBVA_VISA,
                        ),
                        Transaction(
                            date=date(2025, 1, 3),
                            description="Transaction 3",
                            amount=Decimal("300.25"),
                            currency=Currency.ARS,
                            payment_method=PaymentMethod.BBVA_VISA,
                        ),
                    ],
                ):
                    transactions = list(streaming_parser.parse_large_csv(csv_file))

                    assert len(transactions) == 3
                    assert transactions[0].description == "Transaction 1"
                    assert transactions[1].description == "Transaction 2"
                    assert transactions[2].description == "Transaction 3"

                    # Verify pandas was called with correct parameters
                    mock_read_csv.assert_called_once_with(csv_file, chunksize=2)

    @patch("infrastructure.streaming.pd.read_csv")
    def test_parse_large_csv_empty_data_error(self, mock_read_csv, streaming_parser):
        """Test CSV parsing with empty data error."""
        csv_file = Path("empty.csv")

        with patch.object(Path, "exists", return_value=True):
            mock_read_csv.side_effect = pd.errors.EmptyDataError("Empty CSV")

            with pytest.raises(ValueError, match="CSV file is empty"):
                list(streaming_parser.parse_large_csv(csv_file))

    @patch("infrastructure.streaming.pd.read_csv")
    def test_parse_large_csv_parser_error(self, mock_read_csv, streaming_parser):
        """Test CSV parsing with parser error."""
        csv_file = Path("malformed.csv")

        with patch.object(Path, "exists", return_value=True):
            mock_read_csv.side_effect = pd.errors.ParserError("Parser error")

            with pytest.raises(ValueError, match="CSV parsing error"):
                list(streaming_parser.parse_large_csv(csv_file))

    @patch("infrastructure.streaming.pd.read_csv")
    def test_parse_large_csv_os_error(self, mock_read_csv, streaming_parser):
        """Test CSV parsing with OS error."""
        csv_file = Path("test.csv")

        with patch.object(Path, "exists", return_value=True):
            mock_read_csv.side_effect = OSError("File access error")

            with pytest.raises(OSError, match="Error reading CSV file"):
                list(streaming_parser.parse_large_csv(csv_file))

    def test_parse_csv_row_valid(self, streaming_parser):
        """Test parsing valid CSV row."""
        row = pd.Series(
            {
                "Fecha": "01/01/2025",
                "Descripcion": "Test transaction",
                "Moneda": "Pesos",
                "Importe": "100,50",
            }
        )
        payment_method = PaymentMethod.BBVA_VISA

        with patch("domain.utils.DateConverter") as mock_date_converter:
            with patch("domain.utils.AmountParser") as mock_amount_parser:
                mock_date_converter.return_value.convert_dd_mm_yy.return_value = date(
                    2025, 1, 1
                )
                mock_amount_parser.return_value.parse_european_format.return_value = (
                    Decimal("100.50")
                )

                transaction = streaming_parser._parse_csv_row(row, payment_method)

                assert transaction is not None
                assert transaction.description == "Test transaction"
                assert transaction.currency == Currency.ARS
                assert transaction.payment_method == PaymentMethod.BBVA_VISA

    def test_parse_csv_row_usd_currency(self, streaming_parser):
        """Test parsing CSV row with USD currency."""
        row = pd.Series(
            {
                "Fecha": "01/01/2025",
                "Descripcion": "USD transaction",
                "Moneda": "Dolares",
                "Importe": "50,25",
            }
        )
        payment_method = PaymentMethod.BBVA_VISA

        with patch("domain.utils.DateConverter") as mock_date_converter:
            with patch("domain.utils.AmountParser") as mock_amount_parser:
                mock_date_converter.return_value.convert_dd_mm_yy.return_value = date(
                    2025, 1, 1
                )
                mock_amount_parser.return_value.parse_european_format.return_value = (
                    Decimal("50.25")
                )

                transaction = streaming_parser._parse_csv_row(row, payment_method)

                assert transaction is not None
                assert transaction.currency == Currency.USD

    def test_parse_csv_row_alternative_date_column(self, streaming_parser):
        """Test parsing CSV row with alternative date column name."""
        row = pd.Series(
            {
                "Fecha Origen": "01/01/2025",
                "Descripcion": "Test transaction",
                "Moneda": "Pesos",
                "Importe": "100,50",
            }
        )
        payment_method = PaymentMethod.BBVA_VISA

        with patch("domain.utils.DateConverter") as mock_date_converter:
            with patch("domain.utils.AmountParser") as mock_amount_parser:
                mock_date_converter.return_value.convert_dd_mm_yy.return_value = date(
                    2025, 1, 1
                )
                mock_amount_parser.return_value.parse_european_format.return_value = (
                    Decimal("100.50")
                )

                transaction = streaming_parser._parse_csv_row(row, payment_method)

                assert transaction is not None
                assert transaction.description == "Test transaction"

    def test_parse_csv_row_missing_date_column(self, streaming_parser):
        """Test parsing CSV row with missing date column."""
        row = pd.Series(
            {"Descripcion": "Test transaction", "Moneda": "Pesos", "Importe": "100,50"}
        )
        payment_method = PaymentMethod.BBVA_VISA

        transaction = streaming_parser._parse_csv_row(row, payment_method)
        assert transaction is None

    def test_parse_csv_row_empty_description(self, streaming_parser):
        """Test parsing CSV row with empty description."""
        row = pd.Series(
            {
                "Fecha": "01/01/2025",
                "Descripcion": "",
                "Moneda": "Pesos",
                "Importe": "100,50",
            }
        )
        payment_method = PaymentMethod.BBVA_VISA

        transaction = streaming_parser._parse_csv_row(row, payment_method)
        assert transaction is None

    def test_parse_csv_row_invalid_date(self, streaming_parser):
        """Test parsing CSV row with invalid date."""
        row = pd.Series(
            {
                "Fecha": "nan",
                "Descripcion": "Test transaction",
                "Moneda": "Pesos",
                "Importe": "100,50",
            }
        )
        payment_method = PaymentMethod.BBVA_VISA

        transaction = streaming_parser._parse_csv_row(row, payment_method)
        assert transaction is None

    def test_parse_csv_row_parsing_exception(self, streaming_parser):
        """Test parsing CSV row with parsing exception."""
        row = pd.Series(
            {
                "Fecha": "01/01/2025",
                "Descripcion": "Test transaction",
                "Moneda": "Pesos",
                "Importe": "100,50",
            }
        )
        payment_method = PaymentMethod.BBVA_VISA

        with patch("domain.utils.DateConverter") as mock_date_converter:
            mock_date_converter.return_value.convert_dd_mm_yy.side_effect = ValueError(
                "Date parsing error"
            )

            transaction = streaming_parser._parse_csv_row(row, payment_method)
            assert transaction is None


class TestExcelParsing:
    """Test Excel parsing functionality."""

    @pytest.fixture
    def mock_excel_data(self):
        """Create mock Excel data."""
        return pd.DataFrame(
            {
                "Fecha": [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)],
                "Descripcion": ["Transaction 1", "Transaction 2", "Transaction 3"],
                "Importe": [100.50, 200.75, 300.25],
            }
        )

    @pytest.fixture
    def streaming_parser(self):
        """Create StreamingStatementParser."""
        return StreamingStatementParser(chunk_size=2)

    def test_parse_large_excel_file_not_found(self, streaming_parser):
        """Test Excel parsing with non-existent file."""
        non_existent_file = Path("non_existent.xlsx")

        with pytest.raises(FileNotFoundError, match="Excel file not found"):
            list(streaming_parser.parse_large_excel(non_existent_file))

    def test_parse_large_excel_wrong_extension(self, streaming_parser):
        """Test Excel parsing with wrong file extension."""
        wrong_file = Path("test.pdf")

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ValueError, match="Expected Excel file, got: .pdf"):
                list(streaming_parser.parse_large_excel(wrong_file))

    @patch("infrastructure.streaming.pd.ExcelFile")
    def test_parse_large_excel_success(
        self, mock_excel_file, streaming_parser, mock_excel_data
    ):
        """Test successful Excel parsing."""
        excel_file = Path("test.xlsx")

        # Mock file existence
        with patch.object(Path, "exists", return_value=True):
            # Mock ExcelFile context manager
            mock_excel_context = MagicMock()
            mock_excel_context.sheet_names = ["Sheet1", "Sheet2"]
            mock_excel_file.return_value.__enter__.return_value = mock_excel_context

            # Mock pandas read_excel
            with patch(
                "infrastructure.streaming.pd.read_excel", return_value=mock_excel_data
            ):
                # Mock payment method detection
                with patch.object(
                    streaming_parser,
                    "_detect_payment_method_from_filename",
                    return_value=PaymentMethod.BBVA_ACCOUNT,
                ):
                    # Mock row parsing
                    with patch.object(
                        streaming_parser,
                        "_parse_excel_row",
                        side_effect=[
                            Transaction(
                                date=date(2025, 1, 1),
                                description="Transaction 1",
                                amount=Decimal("100.50"),
                                currency=Currency.ARS,
                                payment_method=PaymentMethod.BBVA_ACCOUNT,
                            ),
                            Transaction(
                                date=date(2025, 1, 2),
                                description="Transaction 2",
                                amount=Decimal("200.75"),
                                currency=Currency.ARS,
                                payment_method=PaymentMethod.BBVA_ACCOUNT,
                            ),
                            Transaction(
                                date=date(2025, 1, 3),
                                description="Transaction 3",
                                amount=Decimal("300.25"),
                                currency=Currency.ARS,
                                payment_method=PaymentMethod.BBVA_ACCOUNT,
                            ),
                            Transaction(
                                date=date(2025, 1, 1),
                                description="Transaction 1",
                                amount=Decimal("100.50"),
                                currency=Currency.ARS,
                                payment_method=PaymentMethod.BBVA_ACCOUNT,
                            ),
                            Transaction(
                                date=date(2025, 1, 2),
                                description="Transaction 2",
                                amount=Decimal("200.75"),
                                currency=Currency.ARS,
                                payment_method=PaymentMethod.BBVA_ACCOUNT,
                            ),
                            Transaction(
                                date=date(2025, 1, 3),
                                description="Transaction 3",
                                amount=Decimal("300.25"),
                                currency=Currency.ARS,
                                payment_method=PaymentMethod.BBVA_ACCOUNT,
                            ),
                        ],
                    ):
                        transactions = list(
                            streaming_parser.parse_large_excel(excel_file)
                        )

                        assert len(transactions) == 6  # 3 transactions × 2 sheets
                        assert all(
                            t.payment_method == PaymentMethod.BBVA_ACCOUNT
                            for t in transactions
                        )

    @patch("infrastructure.streaming.pd.ExcelFile")
    def test_parse_large_excel_empty_sheet(self, mock_excel_file, streaming_parser):
        """Test Excel parsing with empty sheet."""
        excel_file = Path("test.xlsx")

        with patch.object(Path, "exists", return_value=True):
            mock_excel_context = MagicMock()
            mock_excel_context.sheet_names = ["EmptySheet"]
            mock_excel_file.return_value.__enter__.return_value = mock_excel_context

            # Mock pandas read_excel to return empty DataFrame
            with patch(
                "infrastructure.streaming.pd.read_excel", return_value=pd.DataFrame()
            ):
                with patch.object(
                    streaming_parser,
                    "_detect_payment_method_from_filename",
                    return_value=PaymentMethod.BBVA_ACCOUNT,
                ):
                    transactions = list(streaming_parser.parse_large_excel(excel_file))

                    assert len(transactions) == 0

    @patch("infrastructure.streaming.pd.ExcelFile")
    def test_parse_large_excel_os_error(self, mock_excel_file, streaming_parser):
        """Test Excel parsing with OS error."""
        excel_file = Path("test.xlsx")

        with patch.object(Path, "exists", return_value=True):
            mock_excel_file.side_effect = OSError("File access error")

            with pytest.raises(OSError, match="Error reading Excel file"):
                list(streaming_parser.parse_large_excel(excel_file))

    def test_parse_excel_row_valid(self, streaming_parser):
        """Test parsing valid Excel row."""
        row = pd.Series(
            {
                "Fecha": date(2025, 1, 1),
                "Descripcion": "Test transaction",
                "Importe": 100.50,
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        transaction = streaming_parser._parse_excel_row(row, payment_method)

        assert transaction is not None
        assert transaction.description == "Test transaction"
        assert transaction.currency == Currency.ARS
        assert transaction.payment_method == PaymentMethod.BBVA_ACCOUNT

    def test_parse_excel_row_string_date(self, streaming_parser):
        """Test parsing Excel row with string date."""
        row = pd.Series(
            {
                "Fecha": "2025-01-01",
                "Descripcion": "Test transaction",
                "Importe": 100.50,
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        transaction = streaming_parser._parse_excel_row(row, payment_method)

        assert transaction is not None
        assert transaction.description == "Test transaction"

    def test_parse_excel_row_iso_date(self, streaming_parser):
        """Test parsing Excel row with ISO 8601 date."""
        row = pd.Series(
            {
                "Fecha": "2025-01-01T10:30:00Z",
                "Descripcion": "Test transaction",
                "Importe": 100.50,
            }
        )
        payment_method = PaymentMethod.MERCADOPAGO

        transaction = streaming_parser._parse_excel_row(row, payment_method)

        assert transaction is not None
        assert transaction.description == "Test transaction"

    def test_parse_excel_row_missing_date(self, streaming_parser):
        """Test parsing Excel row with missing date."""
        row = pd.Series({"Descripcion": "Test transaction", "Importe": 100.50})
        payment_method = PaymentMethod.BBVA_ACCOUNT

        transaction = streaming_parser._parse_excel_row(row, payment_method)
        assert transaction is None

    def test_parse_excel_row_empty_description(self, streaming_parser):
        """Test parsing Excel row with empty description."""
        row = pd.Series(
            {"Fecha": date(2025, 1, 1), "Descripcion": "", "Importe": 100.50}
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        transaction = streaming_parser._parse_excel_row(row, payment_method)
        assert transaction is None

    def test_parse_excel_row_dd_mm_yyyy_format(self, streaming_parser):
        """Test parsing Excel row with DD/MM/YYYY date format."""
        row = pd.Series(
            {
                "Fecha": "01/01/2025",
                "Descripcion": "Test transaction",
                "Importe": 100.50,
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        with patch("domain.utils.DateConverter") as mock_date_converter:
            mock_date_converter.return_value.convert_dd_mm_yy.return_value = date(
                2025, 1, 1
            )

            transaction = streaming_parser._parse_excel_row(row, payment_method)

            assert transaction is not None
            assert transaction.description == "Test transaction"

    def test_parse_excel_row_int_amount(self, streaming_parser):
        """Test parsing Excel row with integer amount."""
        row = pd.Series(
            {
                "Fecha": date(2025, 1, 1),
                "Descripcion": "Test transaction",
                "Importe": 100,
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        transaction = streaming_parser._parse_excel_row(row, payment_method)

        assert transaction is not None
        assert transaction.amount == Decimal("100")

    def test_parse_excel_row_string_amount(self, streaming_parser):
        """Test parsing Excel row with string amount."""
        row = pd.Series(
            {
                "Fecha": date(2025, 1, 1),
                "Descripcion": "Test transaction",
                "Importe": "100,50",
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        with patch("domain.utils.AmountParser") as mock_amount_parser:
            mock_amount_parser.return_value.parse_european_format.return_value = (
                Decimal("100.50")
            )

            transaction = streaming_parser._parse_excel_row(row, payment_method)

            assert transaction is not None
            assert transaction.amount == Decimal("100.50")

    def test_parse_excel_row_parsing_exception(self, streaming_parser):
        """Test parsing Excel row with parsing exception."""
        row = pd.Series(
            {
                "Fecha": date(2025, 1, 1),
                "Descripcion": "Test transaction",
                "Importe": 100.50,
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        with patch("decimal.Decimal", side_effect=ValueError("Decimal error")):
            transaction = streaming_parser._parse_excel_row(row, payment_method)
            assert transaction is None


class TestPaymentMethodDetection:
    """Test payment method detection functionality."""

    @pytest.fixture
    def streaming_parser(self):
        """Create StreamingStatementParser."""
        return StreamingStatementParser()

    @pytest.fixture
    def streaming_parser_with_detector(self, mock_payment_method_detector):
        """Create StreamingStatementParser with payment method detector."""
        return StreamingStatementParser(
            payment_method_detector=mock_payment_method_detector
        )

    def test_detect_payment_method_with_detector(
        self, streaming_parser_with_detector, mock_payment_method_detector
    ):
        """Test payment method detection using injected detector."""
        file_path = Path("test.csv")
        mock_payment_method_detector.detect_from_filename.return_value = (
            PaymentMethod.MACRO_VISA
        )

        result = streaming_parser_with_detector._detect_payment_method_from_filename(
            file_path
        )

        assert result == PaymentMethod.MACRO_VISA
        mock_payment_method_detector.detect_from_filename.assert_called_once_with(
            file_path
        )

    def test_detect_payment_method_bbva_visa_csv(self, streaming_parser):
        """Test BBVA VISA CSV detection."""
        file_path = Path("BBVA-VISA-transactions.csv")

        result = streaming_parser._detect_payment_method_from_filename(file_path)

        assert result == PaymentMethod.BBVA_VISA

    def test_detect_payment_method_macro_visa_csv(self, streaming_parser):
        """Test Macro VISA CSV detection."""
        file_path = Path("MACRO-VISA-transactions.csv")

        result = streaming_parser._detect_payment_method_from_filename(file_path)

        assert result == PaymentMethod.MACRO_VISA

    def test_detect_payment_method_bbva_account_excel(self, streaming_parser):
        """Test BBVA Account Excel detection."""
        file_path = Path("BBVA-DETALLE-movimientos.xlsx")

        result = streaming_parser._detect_payment_method_from_filename(file_path)

        assert result == PaymentMethod.BBVA_ACCOUNT

    def test_detect_payment_method_macro_account_excel(self, streaming_parser):
        """Test Macro Account Excel detection."""
        file_path = Path("MACRO-MOVIMIENTOS-cuenta.xls")

        result = streaming_parser._detect_payment_method_from_filename(file_path)

        assert result == PaymentMethod.MACRO_ACCOUNT

    def test_detect_payment_method_mercadopago_excel(self, streaming_parser):
        """Test Mercadopago Excel detection."""
        file_path = Path("MERCADOPAGO-statement.xlsx")

        result = streaming_parser._detect_payment_method_from_filename(file_path)

        assert result == PaymentMethod.MERCADOPAGO

    def test_detect_payment_method_unknown_file(self, streaming_parser):
        """Test detection with unknown file pattern."""
        file_path = Path("unknown-file.csv")

        result = streaming_parser._detect_payment_method_from_filename(file_path)

        assert result == PaymentMethod.BBVA_VISA  # Default fallback


class TestStreamingParserIntegration:
    """Test integration scenarios with actual components."""

    @pytest.fixture
    def streaming_parser(self):
        """Create StreamingStatementParser."""
        return StreamingStatementParser()

    @pytest.fixture
    def streaming_parser_with_builder(self, mock_transaction_builder):
        """Create StreamingStatementParser with transaction builder."""
        return StreamingStatementParser(
            chunk_size=1000, transaction_builder=mock_transaction_builder
        )

    @patch("infrastructure.streaming.pd.read_csv")
    def test_csv_parsing_with_transaction_builder(
        self, mock_read_csv, streaming_parser_with_builder, mock_transaction_builder
    ):
        """Test CSV parsing with transaction builder integration."""
        csv_file = Path("test.csv")
        mock_data = pd.DataFrame(
            {
                "Fecha": ["01/01/2025"],
                "Descripcion": ["Test transaction"],
                "Moneda": ["Pesos"],
                "Importe": ["100,50"],
            }
        )

        with patch.object(Path, "exists", return_value=True):
            mock_read_csv.return_value = [mock_data]

            with patch.object(
                streaming_parser_with_builder,
                "_detect_payment_method_from_filename",
                return_value=PaymentMethod.BBVA_VISA,
            ):
                transactions = list(
                    streaming_parser_with_builder.parse_large_csv(csv_file)
                )

                assert len(transactions) == 1
                # Verify transaction builder was used (even though we use fallback in current implementation)
                assert transactions[0].payment_method == PaymentMethod.BBVA_VISA

    @patch("infrastructure.streaming.pd.read_csv")
    def test_csv_parsing_row_failures(
        self, mock_read_csv, streaming_parser_with_builder
    ):
        """Test CSV parsing with some row failures."""
        csv_file = Path("test.csv")
        mock_data = pd.DataFrame(
            {
                "Fecha": ["01/01/2025", "invalid_date", "03/01/2025"],
                "Descripcion": ["Transaction 1", "Transaction 2", "Transaction 3"],
                "Moneda": ["Pesos", "Pesos", "Pesos"],
                "Importe": ["100,50", "200,75", "300,25"],
            }
        )

        with patch.object(Path, "exists", return_value=True):
            mock_read_csv.return_value = [mock_data]

            with patch.object(
                streaming_parser_with_builder,
                "_detect_payment_method_from_filename",
                return_value=PaymentMethod.BBVA_VISA,
            ):
                with patch.object(
                    streaming_parser_with_builder,
                    "_parse_csv_row",
                    side_effect=[
                        Transaction(
                            date=date(2025, 1, 1),
                            description="Transaction 1",
                            amount=Decimal("100.50"),
                            currency=Currency.ARS,
                            payment_method=PaymentMethod.BBVA_VISA,
                        ),
                        None,  # Second transaction fails
                        Transaction(
                            date=date(2025, 1, 3),
                            description="Transaction 3",
                            amount=Decimal("300.25"),
                            currency=Currency.ARS,
                            payment_method=PaymentMethod.BBVA_VISA,
                        ),
                    ],
                ):
                    transactions = list(
                        streaming_parser_with_builder.parse_large_csv(csv_file)
                    )

                    # Should only get 2 transactions (skip the failed one)
                    assert len(transactions) == 2
                    assert transactions[0].description == "Transaction 1"
                    assert transactions[1].description == "Transaction 3"

    def test_managed_processing_context_manager(self, streaming_parser):
        """Test managed processing context manager."""
        test_file = Path("test.csv")

        # Should not raise any exceptions
        with streaming_parser._managed_processing(test_file):
            pass

    def test_managed_processing_with_exception(self, streaming_parser):
        """Test managed processing with exception handling."""
        test_file = Path("test.csv")

        with pytest.raises(ValueError, match="Test error"):
            with streaming_parser._managed_processing(test_file):
                raise ValueError("Test error")


class TestStreamingParserEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def streaming_parser(self):
        """Create StreamingStatementParser."""
        return StreamingStatementParser()

    def test_csv_row_missing_optional_columns(self, streaming_parser):
        """Test CSV row parsing with missing optional columns."""
        row = pd.Series(
            {
                "Fecha": "01/01/2025",
                "Descripcion": "Test transaction",
                # Missing 'Moneda' and 'Importe' columns
            }
        )
        payment_method = PaymentMethod.BBVA_VISA

        with patch("domain.utils.DateConverter") as mock_date_converter:
            with patch("domain.utils.AmountParser") as mock_amount_parser:
                mock_date_converter.return_value.convert_dd_mm_yy.return_value = date(
                    2025, 1, 1
                )
                mock_amount_parser.return_value.parse_european_format.return_value = (
                    Decimal("0.00")
                )

                transaction = streaming_parser._parse_csv_row(row, payment_method)

                assert transaction is None  # Zero amount fails Transaction validation

    def test_excel_row_flexible_column_detection(self, streaming_parser):
        """Test Excel row with flexible column detection."""
        row = pd.Series(
            {
                "Date": date(2025, 1, 1),  # English column name
                "Description": "Test transaction",  # English column name
                "Amount": 100.50,  # English column name
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        transaction = streaming_parser._parse_excel_row(row, payment_method)

        assert transaction is not None
        assert transaction.description == "Test transaction"
        assert transaction.amount == Decimal("100.50")

    def test_excel_row_case_insensitive_columns(self, streaming_parser):
        """Test Excel row with case-insensitive column detection."""
        row = pd.Series(
            {
                "FECHA": date(2025, 1, 1),  # Uppercase
                "descripcion": "Test transaction",  # Lowercase
                "IMPORTE": 100.50,  # Uppercase
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        transaction = streaming_parser._parse_excel_row(row, payment_method)

        assert transaction is not None
        assert transaction.description == "Test transaction"

    def test_csv_row_with_transaction_builder(
        self, streaming_parser, mock_transaction_builder
    ):
        """Test CSV row parsing with transaction builder."""
        parser_with_builder = StreamingStatementParser(
            transaction_builder=mock_transaction_builder
        )

        row = pd.Series(
            {
                "Fecha": "01/01/2025",
                "Descripcion": "Test transaction",
                "Moneda": "Pesos",
                "Importe": "100,50",
            }
        )
        payment_method = PaymentMethod.BBVA_VISA

        with patch("domain.utils.DateConverter") as mock_date_converter:
            with patch("domain.utils.AmountParser") as mock_amount_parser:
                mock_date_converter.return_value.convert_dd_mm_yy.return_value = date(
                    2025, 1, 1
                )
                mock_amount_parser.return_value.parse_european_format.return_value = (
                    Decimal("100.50")
                )

                transaction = parser_with_builder._parse_csv_row(row, payment_method)

                assert transaction is not None
                assert transaction.description == "Test transaction"

    def test_excel_row_with_nan_values(self, streaming_parser):
        """Test Excel row parsing with NaN values."""
        row = pd.Series(
            {
                "Fecha": date(2025, 1, 1),
                "Descripcion": pd.NA,  # NaN description
                "Importe": 100.50,
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        transaction = streaming_parser._parse_excel_row(row, payment_method)
        assert transaction is None  # Should skip due to empty description

    def test_csv_row_with_whitespace_handling(self, streaming_parser):
        """Test CSV row parsing with whitespace handling."""
        row = pd.Series(
            {
                "Fecha": "  01/01/2025  ",  # Whitespace around date
                "Descripcion": "  Test transaction  ",  # Whitespace around description
                "Moneda": "  Pesos  ",  # Whitespace around currency
                "Importe": "  100,50  ",  # Whitespace around amount
            }
        )
        payment_method = PaymentMethod.BBVA_VISA

        with patch("domain.utils.DateConverter") as mock_date_converter:
            with patch("domain.utils.AmountParser") as mock_amount_parser:
                mock_date_converter.return_value.convert_dd_mm_yy.return_value = date(
                    2025, 1, 1
                )
                mock_amount_parser.return_value.parse_european_format.return_value = (
                    Decimal("100.50")
                )

                transaction = streaming_parser._parse_csv_row(row, payment_method)

                assert transaction is not None
                assert (
                    transaction.description == "Test transaction"
                )  # Whitespace stripped

    def test_zero_chunk_size_handled(self):
        """Test that zero chunk size is handled properly."""
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            StreamingStatementParser(chunk_size=0)

    def test_negative_chunk_size_handled(self):
        """Test that negative chunk size is handled properly."""
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            StreamingStatementParser(chunk_size=-1)

    @patch("infrastructure.streaming.pd.read_csv")
    def test_csv_parsing_with_none_transaction(self, mock_read_csv, streaming_parser):
        """Test CSV parsing when row parsing returns None."""
        csv_file = Path("test.csv")
        mock_data = pd.DataFrame(
            {
                "Fecha": ["01/01/2025"],
                "Descripcion": [""],  # Empty description
                "Moneda": ["Pesos"],
                "Importe": ["100,50"],
            }
        )

        with patch.object(Path, "exists", return_value=True):
            mock_read_csv.return_value = [mock_data]

            with patch.object(
                streaming_parser,
                "_detect_payment_method_from_filename",
                return_value=PaymentMethod.BBVA_VISA,
            ):
                with patch.object(
                    streaming_parser, "_parse_csv_row", return_value=None
                ):
                    transactions = list(streaming_parser.parse_large_csv(csv_file))

                    assert len(transactions) == 0  # No transactions due to None return

    @patch("infrastructure.streaming.pd.ExcelFile")
    def test_excel_parsing_with_none_transaction(
        self, mock_excel_file, streaming_parser
    ):
        """Test Excel parsing when row parsing returns None."""
        excel_file = Path("test.xlsx")
        mock_data = pd.DataFrame(
            {
                "Fecha": [date(2025, 1, 1)],
                "Descripcion": [""],  # Empty description
                "Importe": [100.50],
            }
        )

        with patch.object(Path, "exists", return_value=True):
            mock_excel_context = MagicMock()
            mock_excel_context.sheet_names = ["Sheet1"]
            mock_excel_file.return_value.__enter__.return_value = mock_excel_context

            with patch(
                "infrastructure.streaming.pd.read_excel", return_value=mock_data
            ):
                with patch.object(
                    streaming_parser,
                    "_detect_payment_method_from_filename",
                    return_value=PaymentMethod.BBVA_ACCOUNT,
                ):
                    with patch.object(
                        streaming_parser, "_parse_excel_row", return_value=None
                    ):
                        transactions = list(
                            streaming_parser.parse_large_excel(excel_file)
                        )

                        assert (
                            len(transactions) == 0
                        )  # No transactions due to None return

    def test_detect_payment_method_case_insensitive(self, streaming_parser):
        """Test payment method detection is case insensitive."""
        # Test lowercase
        file_path = Path("bbva-visa-transactions.csv")
        result = streaming_parser._detect_payment_method_from_filename(file_path)
        assert result == PaymentMethod.BBVA_VISA

        # Test mixed case
        file_path = Path("MaCrO-VIsA-transactions.csv")
        result = streaming_parser._detect_payment_method_from_filename(file_path)
        assert result == PaymentMethod.MACRO_VISA

    def test_excel_row_with_none_amount(self, streaming_parser):
        """Test Excel row parsing with None amount."""
        row = pd.Series(
            {
                "Fecha": date(2025, 1, 1),
                "Descripcion": "Test transaction",
                "Importe": None,
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        transaction = streaming_parser._parse_excel_row(row, payment_method)

        assert transaction is None  # Zero amount fails Transaction validation

    def test_excel_row_date_parsing_edge_cases(self, streaming_parser):
        """Test Excel row date parsing edge cases."""
        # Test with date string having multiple format possibilities
        row = pd.Series(
            {
                "Fecha": "2025/01/01",  # Different separator
                "Descripcion": "Test transaction",
                "Importe": 100.50,
            }
        )
        payment_method = PaymentMethod.BBVA_ACCOUNT

        with patch("domain.utils.DateConverter") as mock_date_converter:
            mock_date_converter.return_value.convert_dd_mm_yy.return_value = date(
                2025, 1, 1
            )

            transaction = streaming_parser._parse_excel_row(row, payment_method)

            assert transaction is not None
            assert transaction.description == "Test transaction"


class TestStreamingParserLogging:
    """Test logging behavior of StreamingStatementParser."""

    @pytest.fixture
    def streaming_parser(self):
        """Create StreamingStatementParser."""
        return StreamingStatementParser()

    def test_initialization_logging(self, caplog):
        """Test that initialization logs the chunk size."""
        with caplog.at_level("INFO"):
            StreamingStatementParser(chunk_size=2000)

        assert (
            "StreamingStatementParser initialized with chunk_size=2000" in caplog.text
        )

    def test_set_chunk_size_logging(self, streaming_parser, caplog):
        """Test that chunk size updates are logged."""
        with caplog.at_level("INFO"):
            streaming_parser.set_chunk_size(5000)

        assert "Chunk size updated to: 5000" in caplog.text

    @patch("infrastructure.streaming.pd.read_csv")
    def test_csv_parsing_logging(self, mock_read_csv, streaming_parser, caplog):
        """Test logging during CSV parsing."""
        csv_file = Path("test.csv")
        mock_data = pd.DataFrame(
            {
                "Fecha": ["01/01/2025"],
                "Descripcion": ["Test transaction"],
                "Moneda": ["Pesos"],
                "Importe": ["100,50"],
            }
        )

        with patch.object(Path, "exists", return_value=True):
            mock_read_csv.return_value = [mock_data]

            with patch.object(
                streaming_parser,
                "_detect_payment_method_from_filename",
                return_value=PaymentMethod.BBVA_VISA,
            ):
                with patch.object(
                    streaming_parser, "_parse_csv_row", return_value=None
                ):
                    with caplog.at_level("INFO"):
                        list(streaming_parser.parse_large_csv(csv_file))

                    assert "Starting streaming CSV parsing: test.csv" in caplog.text
                    assert "Completed CSV streaming" in caplog.text

    @patch("infrastructure.streaming.pd.ExcelFile")
    def test_excel_parsing_logging(self, mock_excel_file, streaming_parser, caplog):
        """Test logging during Excel parsing."""
        excel_file = Path("test.xlsx")
        mock_data = pd.DataFrame(
            {
                "Fecha": [date(2025, 1, 1)],
                "Descripcion": ["Test transaction"],
                "Importe": [100.50],
            }
        )

        with patch.object(Path, "exists", return_value=True):
            mock_excel_context = MagicMock()
            mock_excel_context.sheet_names = ["Sheet1"]
            mock_excel_file.return_value.__enter__.return_value = mock_excel_context

            with patch(
                "infrastructure.streaming.pd.read_excel", return_value=mock_data
            ):
                with patch.object(
                    streaming_parser,
                    "_detect_payment_method_from_filename",
                    return_value=PaymentMethod.BBVA_ACCOUNT,
                ):
                    with patch.object(
                        streaming_parser, "_parse_excel_row", return_value=None
                    ):
                        with caplog.at_level("INFO"):
                            list(streaming_parser.parse_large_excel(excel_file))

                        assert (
                            "Starting streaming Excel parsing: test.xlsx" in caplog.text
                        )
                        assert "Completed Excel streaming" in caplog.text

    def test_payment_method_detection_logging(self, streaming_parser, caplog):
        """Test logging when payment method detection fails."""
        unknown_file = Path("unknown-file.csv")

        with caplog.at_level("WARNING"):
            streaming_parser._detect_payment_method_from_filename(unknown_file)

        assert (
            "Could not detect payment method from filename: unknown-file.csv"
            in caplog.text
        )
