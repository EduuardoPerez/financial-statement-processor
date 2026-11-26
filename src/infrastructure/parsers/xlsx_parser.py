"""
XLSX statement parser implementation for the Financial Statement Processor.

This module provides a concrete implementation of the StatementParser interface
for processing XLSX financial statements, specifically for Mercadopago statements.

Classes:
    XLSXStatementParser: XLSX statement parser using pandas for data extraction
"""

from pathlib import Path
from typing import Any

import pandas as pd

from domain.builders import TransactionBuilder
from domain.models import (
    Currency,
    ExtractionResult,
    PaymentMethod,
    Statement,
    Transaction,
)
from domain.services import StatementParser

from ._shared import (
    extraction_for_file,
    is_blank_row,
    retain_transaction,
    source_text,
    verify_file_unchanged,
)


class XLSXStatementParser(StatementParser):
    """
    XLSX statement parser using pandas for data extraction.

    This parser handles XLSX financial statements by loading structured
    data and creating Statement objects. It serves as a concrete implementation
    of the StatementParser strategy interface, specifically designed for
    Mercadopago XLSX statements.

    The parser is responsible for:
    1. Detecting XLSX files by extension (case-insensitive)
    2. Loading structured data from XLSX files using pandas
    3. Creating Statement objects with detected payment method
    4. Parsing Mercadopago transaction data with ISO 8601 timestamps

    Example:
        >>> detector = SomePaymentMethodDetector()
        >>> parser = XLSXStatementParser(detector, transaction_builder)
        >>> can_parse = parser.can_parse(Path("statement.XLSX"))
        >>> assert can_parse is True
        >>> statement = parser.parse(Path("mercadopago.xlsx"))
        >>> assert isinstance(statement, Statement)
    """

    def __init__(self, detector: Any, transaction_builder: TransactionBuilder) -> None:
        """
        Initialize XLSX parser with payment method detector and transaction builder.

        Args:
            detector: Payment method detector for identifying bank/card type
                     from XLSX content or filename
            transaction_builder: TransactionBuilder for constructing Transaction
                                objects from parsed XLSX data
        """
        self._detector = detector
        self._transaction_builder = transaction_builder

    def can_parse(self, file_path: Path) -> bool:
        """
        Determine if this parser can handle the given file.

        Checks if the file has an XLSX extension (case-insensitive).

        Args:
            file_path: Path to the file to be parsed

        Returns:
            True if file has .xlsx extension (case-insensitive), False otherwise

        Example:
            >>> parser = XLSXStatementParser(detector, transaction_builder)
            >>> assert parser.can_parse(Path("statement.xlsx")) is True
            >>> assert parser.can_parse(Path("statement.XLSX")) is True
            >>> assert parser.can_parse(Path("statement.pdf")) is False
        """
        return file_path.suffix.lower() == ".xlsx"

    def parse(self, file_path: Path) -> Statement:
        """
        Parse the XLSX file and return a Statement object with transactions.

        Loads structured data from the XLSX file using pandas and creates a
        Statement object with the detected payment method and parsed transactions.
        Supports Mercadopago XLSX format with ISO 8601 timestamps.

        Args:
            file_path: Path to the XLSX file to parse

        Returns:
            Statement object with detected payment method and parsed transactions

        Raises:
            FileNotFoundError: If the input file does not exist
            ValueError: If the file format is invalid or cannot be parsed
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during file processing

        Example:
            >>> parser = XLSXStatementParser(detector, transaction_builder)
            >>> statement = parser.parse(Path("mercadopago.xlsx"))
            >>> assert isinstance(statement, Statement)
            >>> assert len(statement.transactions) > 0
        """
        if not file_path.exists():
            raise FileNotFoundError(f"XLSX file not found: {file_path}")

        try:
            # Detect payment method from filename
            payment_method = self._detector.detect_from_filename(file_path)

            # Load XLSX data
            report = extraction_for_file(file_path)
            df = self._load_xlsx_data(file_path)
            first_data_row = 4 if payment_method == PaymentMethod.BBVA_MASTERCARD else 2

            # Create statement
            statement = Statement(payment_method=payment_method)
            statement.extraction = report

            # Parse transactions based on payment method
            transactions = self._parse_transactions(
                df, payment_method, report, first_data_row
            )

            # Add transactions to statement
            for transaction in transactions:
                statement.add_transaction(transaction)

            verify_file_unchanged(file_path, report)
            return statement

        except PermissionError as e:
            raise PermissionError(
                f"Permission denied reading XLSX file: {file_path}"
            ) from e
        except Exception as e:
            raise OSError(f"Error processing XLSX file {file_path}: {str(e)}") from e

    def get_supported_extensions(self) -> set[str]:
        """
        Return the set of file extensions supported by this parser.

        Returns:
            Set containing '.xlsx' extension

        Example:
            >>> parser = XLSXStatementParser(detector, transaction_builder)
            >>> extensions = parser.get_supported_extensions()
            >>> assert extensions == {'.xlsx'}
        """
        return {".xlsx"}

    def _load_xlsx_data(self, file_path: Path) -> pd.DataFrame:
        """
        Helper method to load structured data from XLSX file using pandas.

        This method handles the low-level XLSX data loading using pandas.
        It handles both Mercadopago format and BBVA Mastercard format.

        Args:
            file_path: Path to the XLSX file

        Returns:
            DataFrame containing the XLSX data

        Raises:
            ValueError: If XLSX file cannot be opened or read
            OSError: If there's an I/O error during loading

        Example:
            >>> parser = XLSXStatementParser(detector, transaction_builder)
            >>> df = parser._load_xlsx_data(Path("mercadopago.xlsx"))
            >>> assert isinstance(df, pd.DataFrame)
            >>> assert len(df.columns) > 0
        """
        try:
            # Check if it's a BBVA Mastercard file that needs special handling
            if (
                "BBVA" in file_path.name.upper()
                and "MASTERCARD" in file_path.name.upper()
            ):
                # Load with third row as header (skip first two rows)
                df = pd.read_excel(
                    file_path,
                    engine="openpyxl",
                    header=2,
                    dtype=object,
                    keep_default_na=False,
                )
            else:
                # Load normally for Mercadopago
                df = pd.read_excel(
                    file_path, engine="openpyxl", dtype=object, keep_default_na=False
                )

            if df.empty:
                raise ValueError(f"No data found in XLSX file: {file_path}")

            return df

        except Exception as e:
            raise ValueError(
                f"Failed to load data from XLSX file {file_path}: {str(e)}"
            ) from e

    def _parse_transactions(
        self,
        df: pd.DataFrame,
        payment_method: PaymentMethod,
        report: ExtractionResult | None = None,
        first_data_row: int = 2,
    ) -> list[Transaction]:
        """
        Parse transaction data from XLSX DataFrame based on payment method.

        Currently supports Mercadopago XLSX format with ISO 8601 timestamps
        and BBVA Mastercard XLSX format with DD/MM/YY dates.

        Args:
            df: DataFrame containing XLSX data
            payment_method: Detected payment method (MERCADOPAGO or BBVA_MASTERCARD)

        Returns:
            List of parsed Transaction objects

        Example:
            >>> transactions = parser._parse_transactions(df, PaymentMethod.MERCADOPAGO)
            >>> assert len(transactions) > 0
        """
        transactions = []

        if payment_method == PaymentMethod.MERCADOPAGO:
            transactions = self._parse_mercadopago_transactions(
                df, report, first_data_row
            )
        elif payment_method == PaymentMethod.BBVA_MASTERCARD:
            transactions = self._parse_bbva_mastercard_transactions(
                df, report, first_data_row
            )

        return transactions

    def _parse_mercadopago_transactions(
        self,
        df: pd.DataFrame,
        report: ExtractionResult | None = None,
        first_data_row: int = 2,
    ) -> list[Transaction]:
        """
        Parse Mercadopago XLSX transactions.

        Mercadopago format:
        - Columns: "Fecha de Pago", "Tipo de Operación", "Importe"
        - Date format: ISO 8601 timestamps (2025-02-01T17:45:36Z)
        - Amount: Already numeric format
        - Currency: Always ARS for Mercadopago
        """
        transactions = []

        # Process each row
        for row_number, (_, row) in enumerate(df.iterrows(), start=first_data_row):
            locator = f"row:{row_number}"
            if is_blank_row(row):
                continue
            raw_date = source_text(row["Fecha de Pago"])
            raw_description = source_text(row["Tipo de Operación"])
            date_str = raw_date.strip()
            operation_type = raw_description.strip()
            amount_str = source_text(row["Importe"])

            try:
                # Convert ISO 8601 timestamp to YYYY-MM-DD format
                # Extract date part from "2025-02-01T17:45:36Z"
                formatted_date = date_str.split("T")[0]

                # Build transaction using TransactionBuilder
                transaction = self._transaction_builder.build_from_xls_data(
                    date_str=formatted_date,
                    description=operation_type,
                    amount_str=amount_str,
                    currency=Currency.ARS,
                    payment_method=PaymentMethod.MERCADOPAGO,
                )
                native_ids = {
                    name: source_text(row[name])
                    for name in (
                        "Número de Movimiento",
                        "Operación Relacionada",
                        "SOURCE_ID",
                    )
                    if name in row and source_text(row[name])
                }
                transactions.append(
                    retain_transaction(
                        transaction,
                        report,
                        locator,
                        raw_date,
                        amount_str,
                        raw_description,
                        native_ids=native_ids,
                    )
                )

            except (ValueError, IndexError, TypeError) as error:
                if report is not None:
                    report.discard(locator, str(error))

        return transactions

    def _parse_bbva_mastercard_transactions(
        self,
        df: pd.DataFrame,
        report: ExtractionResult | None = None,
        first_data_row: int = 2,
    ) -> list[Transaction]:
        """
        Parse BBVA Mastercard XLSX transactions.

        BBVA Mastercard format:
        - Columns: "Fecha y hora", "Movimientos", "Cuota", "Monto"
        - Date format: DD/MM/YY (e.g., "07/07/25")
        - Amount: European format with currency prefix (e.g., "USD 35,00", "$ 107.970,00")
        - Currency: USD prefix or $ for ARS
        """
        transactions = []

        # Process each row
        for row_number, (_, row) in enumerate(df.iterrows(), start=first_data_row):
            locator = f"row:{row_number}"
            if is_blank_row(row):
                continue
            raw_date = source_text(row["Fecha y hora"])
            raw_description = source_text(row["Movimientos"])
            raw_amount = source_text(row["Monto"])
            date_str = raw_date.strip()
            transaction_description = raw_description.strip()
            amount_str = raw_amount.strip()

            try:
                # Parse date from DD/MM/YY to YYYY-MM-DD
                formatted_date = self._convert_bbva_date(date_str)

                # Parse currency and amount from the source string
                currency, amount_str = self._parse_bbva_amount(amount_str)

                # Build transaction using TransactionBuilder
                transaction = self._transaction_builder.build_from_xls_data(
                    date_str=formatted_date,
                    description=transaction_description,
                    amount_str=amount_str,
                    currency=currency,
                    payment_method=PaymentMethod.BBVA_MASTERCARD,
                )
                references = (
                    {"Cuota": source_text(row["Cuota"])}
                    if "Cuota" in row and source_text(row["Cuota"])
                    else {}
                )
                transactions.append(
                    retain_transaction(
                        transaction,
                        report,
                        locator,
                        raw_date,
                        raw_amount,
                        raw_description,
                        raw_currency=(
                            "USD"
                            if raw_amount.startswith("USD ")
                            else "$"
                            if raw_amount.startswith("$ ")
                            else None
                        ),
                        references=references,
                    )
                )

            except (ValueError, IndexError, TypeError) as error:
                if report is not None:
                    report.discard(locator, str(error))

        return transactions

    def _convert_bbva_date(self, date_str: str) -> str:
        """
        Convert BBVA date format from DD/MM/YY to YYYY-MM-DD.

        Args:
            date_str: Date string in DD/MM/YY format (e.g., "07/07/25")

        Returns:
            Date string in YYYY-MM-DD format (e.g., "2025-07-07")
        """
        from datetime import datetime

        # Parse DD/MM/YY format and convert to YYYY-MM-DD
        date_obj = datetime.strptime(date_str, "%d/%m/%y")
        return date_obj.strftime("%Y-%m-%d")

    def _parse_bbva_amount(self, amount_str: str) -> tuple[Currency, str]:
        """
        Parse BBVA amount string to extract currency and amount.

        Args:
            amount_str: Amount string (e.g., "USD 35,00", "$ 107.970,00")

        Returns:
            Tuple of (Currency, amount_string)
        """
        # Clean the string
        amount_clean = amount_str.strip()

        # Check for USD prefix
        if amount_clean.startswith("USD "):
            currency = Currency.USD
            amount_str = amount_clean[4:]  # Remove "USD " prefix
        elif amount_clean.startswith("$ "):
            currency = Currency.ARS
            amount_str = amount_clean[2:]  # Remove "$ " prefix
        else:
            # Default to ARS if no clear currency indicator
            currency = Currency.ARS
            amount_str = amount_clean

        return currency, amount_str
