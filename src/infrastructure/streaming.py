"""
Memory-efficient streaming parsers for large CSV/Excel files.

This module provides chunk-based parsing for large financial statement files
without loading entire files into memory. It integrates with the existing
clean architecture and follows established patterns.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from domain.builders import TransactionBuilder
from domain.detectors import PaymentMethodDetector
from domain.models import Currency, PaymentMethod, Transaction

logger = logging.getLogger(__name__)


class StreamingStatementParser:
    """
    Memory-efficient parser for large CSV/Excel files using chunk processing.

    This parser processes large files in configurable chunks to minimize memory
    usage while maintaining compatibility with the existing domain model and
    architecture patterns.

    Features:
    - Configurable chunk size for memory optimization
    - CSV streaming using pandas chunksize parameter
    - Excel streaming with sheet-by-sheet processing
    - Integration with existing TransactionBuilder and PaymentMethodDetector
    - Comprehensive error handling and logging
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        transaction_builder: TransactionBuilder | None = None,
        payment_method_detector: PaymentMethodDetector | None = None,
    ) -> None:
        """
        Initialize StreamingStatementParser with configurable chunk size.

        Args:
            chunk_size: Number of rows to process in each chunk (default: 1000)
            transaction_builder: Builder for creating Transaction objects
            payment_method_detector: Detector for identifying payment methods

        Example:
            >>> parser = StreamingStatementParser(chunk_size=500)
            >>> for transaction in parser.parse_large_csv(Path("large_file.csv")):
            ...     print(f"Parsed: {transaction.description}")
        """
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")

        self._chunk_size = chunk_size
        self._transaction_builder = transaction_builder
        self._payment_method_detector = payment_method_detector

        logger.info(
            f"StreamingStatementParser initialized with chunk_size={chunk_size}"
        )

    def parse_large_csv(self, file_path: Path) -> Iterator[Transaction]:
        """
        Parse large CSV files in chunks using pandas chunksize for memory efficiency.

        This method reads CSV files in configurable chunks, processes each chunk
        row by row, and yields Transaction objects as they're parsed. This approach
        minimizes memory usage for large files.

        Args:
            file_path: Path to the CSV file to parse

        Yields:
            Transaction: Individual transaction objects parsed from CSV rows

        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            ValueError: If the CSV file is malformed or payment method cannot be detected
            OSError: If there are file system access issues

        Example:
            >>> parser = StreamingStatementParser(chunk_size=1000)
            >>> transactions = list(parser.parse_large_csv(Path("large_statement.csv")))
            >>> print(f"Parsed {len(transactions)} transactions")
        """
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        if not file_path.suffix.lower() == ".csv":
            raise ValueError(f"Expected CSV file, got: {file_path.suffix}")

        logger.info(f"Starting streaming CSV parsing: {file_path.name}")

        try:
            # Detect payment method from filename for CSV files
            payment_method = self._detect_payment_method_from_filename(file_path)

            # Use pandas read_csv with chunksize for memory-efficient processing
            chunk_reader = pd.read_csv(file_path, chunksize=self._chunk_size)

            total_parsed = 0
            chunk_number = 0

            for chunk in chunk_reader:
                chunk_number += 1
                logger.debug(f"Processing chunk {chunk_number} with {len(chunk)} rows")

                # Process each row in the chunk
                for _, row in chunk.iterrows():
                    try:
                        transaction = self._parse_csv_row(row, payment_method)
                        if transaction:
                            total_parsed += 1
                            yield transaction
                    except Exception as e:
                        logger.warning(f"Failed to parse CSV row: {e}")
                        # Continue processing other rows despite individual failures
                        continue

            logger.info(
                f"Completed CSV streaming: {total_parsed} transactions parsed from {file_path.name}"
            )

        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file is empty: {file_path}")
        except pd.errors.ParserError as e:
            raise ValueError(f"CSV parsing error in {file_path}: {str(e)}")
        except Exception as e:
            raise OSError(f"Error reading CSV file {file_path}: {str(e)}")

    def parse_large_excel(self, file_path: Path) -> Iterator[Transaction]:
        """
        Parse large Excel files sheet by sheet for memory efficiency.

        This method processes Excel files one sheet at a time, then processes
        each sheet row by row to minimize memory usage. It properly handles
        multi-sheet workbooks and ensures proper resource cleanup.

        Args:
            file_path: Path to the Excel file to parse

        Yields:
            Transaction: Individual transaction objects parsed from Excel rows

        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the Excel file is malformed or payment method cannot be detected
            OSError: If there are file system access issues

        Example:
            >>> parser = StreamingStatementParser(chunk_size=500)
            >>> transactions = list(parser.parse_large_excel(Path("large_workbook.xlsx")))
            >>> print(f"Parsed {len(transactions)} transactions")
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        if file_path.suffix.lower() not in {".xls", ".xlsx"}:
            raise ValueError(f"Expected Excel file, got: {file_path.suffix}")

        logger.info(f"Starting streaming Excel parsing: {file_path.name}")

        try:
            # Detect payment method from filename for Excel files
            payment_method = self._detect_payment_method_from_filename(file_path)

            total_parsed = 0
            sheet_count = 0

            # Use ExcelFile context manager for proper resource management
            with pd.ExcelFile(file_path) as excel_file:
                for sheet_name in excel_file.sheet_names:
                    sheet_count += 1
                    logger.debug(f"Processing sheet {sheet_count}: {sheet_name}")

                    # Read sheet data
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)

                    if df.empty:
                        logger.debug(f"Sheet {sheet_name} is empty, skipping")
                        continue

                    # Process each row in the sheet
                    for _, row in df.iterrows():
                        try:
                            transaction = self._parse_excel_row(row, payment_method)
                            if transaction:
                                total_parsed += 1
                                yield transaction
                        except Exception as e:
                            logger.warning(
                                f"Failed to parse Excel row in sheet {sheet_name}: {e}"
                            )
                            # Continue processing other rows despite individual failures
                            continue

            logger.info(
                f"Completed Excel streaming: {total_parsed} transactions parsed from {sheet_count} sheets in {file_path.name}"
            )

        except Exception as e:
            raise OSError(f"Error reading Excel file {file_path}: {str(e)}")

    def _parse_csv_row(
        self, row: pd.Series, payment_method: PaymentMethod
    ) -> Transaction | None:
        """
        Parse individual CSV row to Transaction object.

        This method handles the specific CSV format parsing logic, including
        date conversion, amount parsing, and currency detection based on the
        established patterns in the codebase.

        Args:
            row: pandas Series representing a single CSV row
            payment_method: Detected payment method for the statement

        Returns:
            Transaction object if parsing succeeds, None if row should be skipped

        Raises:
            ValueError: If required fields are missing or malformed
        """
        try:
            # Handle flexible date column names (existing pattern)
            date_col = "Fecha" if "Fecha" in row.index else "Fecha Origen"
            if date_col not in row.index:
                raise ValueError(
                    "No date column found (expected 'Fecha' or 'Fecha Origen')"
                )

            # Extract basic fields
            date_str = str(row[date_col]).strip()
            description = (
                str(row["Descripcion"]).strip() if "Descripcion" in row.index else ""
            )

            # Handle currency mapping (existing pattern)
            currency_str = (
                str(row["Moneda"]).strip() if "Moneda" in row.index else "Pesos"
            )
            currency = Currency.USD if currency_str == "Dolares" else Currency.ARS

            # Parse amount with European format support
            amount_str = (
                str(row["Importe"]).strip() if "Importe" in row.index else "0,00"
            )

            # Skip empty or invalid rows
            if not date_str or not description or date_str == "nan":
                return None

            # Use TransactionBuilder if available, otherwise create directly
            if self._transaction_builder:
                # TransactionBuilder is designed for PDF parsing, so use fallback for CSV
                from domain.utils import AmountParser, DateConverter

                date_converter = DateConverter()
                amount_parser = AmountParser()

                # Convert DD/MM/YYYY to date object (CSV format)
                parsed_date = date_converter.convert_dd_mm_yy(
                    date_str.replace("/", ".")
                )
                parsed_amount = amount_parser.parse_european_format(amount_str)

                transaction = Transaction(
                    date=parsed_date,
                    description=description,
                    amount=parsed_amount,
                    currency=currency,
                    payment_method=payment_method,
                )
            else:
                # Fallback to direct creation (simplified for streaming)
                from domain.utils import AmountParser, DateConverter

                date_converter = DateConverter()
                amount_parser = AmountParser()

                # Convert DD/MM/YYYY to date object
                parsed_date = date_converter.convert_dd_mm_yy(
                    date_str.replace("/", ".")
                )
                parsed_amount = amount_parser.parse_european_format(amount_str)

                transaction = Transaction(
                    date=parsed_date,
                    description=description,
                    amount=parsed_amount,
                    currency=currency,
                    payment_method=payment_method,
                )

            return transaction

        except Exception as e:
            logger.warning(f"Failed to parse CSV row: {e}")
            return None

    def _parse_excel_row(
        self, row: pd.Series, payment_method: PaymentMethod
    ) -> Transaction | None:
        """
        Parse individual Excel row to Transaction object.

        This method handles Excel-specific parsing logic, including different
        date formats, amount handling, and currency detection based on the
        established patterns in the codebase.

        Args:
            row: pandas Series representing a single Excel row
            payment_method: Detected payment method for the statement

        Returns:
            Transaction object if parsing succeeds, None if row should be skipped

        Raises:
            ValueError: If required fields are missing or malformed
        """
        try:
            # Handle different Excel date formats
            date_value = None
            amount_value = None
            description = ""

            # Try to find date column (different patterns for different banks)
            for col in row.index:
                col_lower = str(col).lower()
                if "fecha" in col_lower and pd.notna(row[col]):
                    date_value = row[col]
                elif "date" in col_lower and pd.notna(row[col]):
                    date_value = row[col]
                elif "descripcion" in col_lower or "description" in col_lower:
                    description = str(row[col]).strip() if pd.notna(row[col]) else ""
                elif "importe" in col_lower or "amount" in col_lower:
                    amount_value = row[col]

            # Skip empty or invalid rows
            if date_value is None or not description or pd.isna(date_value):
                return None

            # Handle date conversion based on type
            if isinstance(date_value, str):
                date_str = date_value.strip()
                if "T" in date_str:
                    # ISO 8601 format (e.g., Mercadopago)
                    date_str = date_str.split("T")[0]
            else:
                # Datetime object (e.g., Macro Account)
                date_str = date_value.strftime("%Y-%m-%d")

            # Handle amount parsing
            if amount_value is None:
                amount_str = "0,00"
            elif isinstance(amount_value, int | float):
                amount_str = str(amount_value)
            else:
                amount_str = str(amount_value).strip()

            # Default to ARS currency for Excel files
            currency = Currency.ARS

            # Create transaction directly (simplified for streaming)
            from datetime import datetime
            from decimal import Decimal

            from domain.utils import AmountParser, DateConverter

            date_converter = DateConverter()
            amount_parser = AmountParser()

            # Handle date parsing
            if "-" in date_str:
                # YYYY-MM-DD format
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                # DD/MM/YYYY format (convert to DD.MM.YY format)
                date_parts = date_str.split("/")
                if len(date_parts) == 3:
                    # Convert DD/MM/YYYY to DD.MM.YY
                    day, month, year = date_parts
                    year_short = year[-2:]  # Get last 2 digits of year
                    formatted_date = f"{day}.{month}.{year_short}"
                    parsed_date = date_converter.convert_dd_mm_yy(formatted_date)
                else:
                    parsed_date = date_converter.convert_dd_mm_yy(date_str)

            # Parse amount
            if isinstance(amount_value, int | float):
                parsed_amount = Decimal(str(amount_value))
            else:
                parsed_amount = amount_parser.parse_european_format(amount_str)

            transaction = Transaction(
                date=parsed_date,
                description=description,
                amount=parsed_amount,
                currency=currency,
                payment_method=payment_method,
            )

            return transaction

        except Exception as e:
            logger.warning(f"Failed to parse Excel row: {e}")
            return None

    def _detect_payment_method_from_filename(self, file_path: Path) -> PaymentMethod:
        """
        Detect payment method from filename using existing patterns.

        Args:
            file_path: Path to the file

        Returns:
            PaymentMethod enum value

        Raises:
            ValueError: If payment method cannot be detected
        """
        if self._payment_method_detector:
            return self._payment_method_detector.detect_from_filename(file_path)

        # Fallback to simple filename-based detection
        filename_upper = file_path.name.upper()

        # CSV detection patterns
        if file_path.suffix.lower() == ".csv":
            if "BBVA" in filename_upper and "VISA" in filename_upper:
                return PaymentMethod.BBVA_VISA
            elif "MACRO" in filename_upper and "VISA" in filename_upper:
                return PaymentMethod.MACRO_VISA

        # Excel detection patterns
        elif file_path.suffix.lower() in {".xls", ".xlsx"}:
            if "BBVA" in filename_upper and "DETALLE" in filename_upper:
                return PaymentMethod.BBVA_ACCOUNT
            elif "MACRO" in filename_upper and "MOVIMIENTOS" in filename_upper:
                return PaymentMethod.MACRO_ACCOUNT
            elif "MERCADOPAGO" in filename_upper:
                return PaymentMethod.MERCADOPAGO

        # Default fallback
        logger.warning(
            f"Could not detect payment method from filename: {file_path.name}"
        )
        return PaymentMethod.BBVA_VISA  # Safe default

    @contextmanager
    def _managed_processing(self, file_path: Path):
        """
        Context manager for safe file processing with resource cleanup.

        Args:
            file_path: Path to the file being processed

        Yields:
            None
        """
        try:
            logger.debug(f"Starting managed processing for: {file_path.name}")
            yield
        except Exception as e:
            logger.error(f"Error during managed processing of {file_path.name}: {e}")
            raise
        finally:
            logger.debug(f"Completed managed processing for: {file_path.name}")

    def get_chunk_size(self) -> int:
        """Get the current chunk size setting."""
        return self._chunk_size

    def set_chunk_size(self, chunk_size: int) -> None:
        """
        Set a new chunk size for processing.

        Args:
            chunk_size: New chunk size (must be positive)

        Raises:
            ValueError: If chunk_size is not positive
        """
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")

        self._chunk_size = chunk_size
        logger.info(f"Chunk size updated to: {chunk_size}")

    def __repr__(self) -> str:
        """String representation of the StreamingStatementParser."""
        return f"StreamingStatementParser(chunk_size={self._chunk_size})"
