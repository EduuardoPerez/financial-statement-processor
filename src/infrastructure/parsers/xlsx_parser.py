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
from domain.models import Currency, PaymentMethod, Statement, Transaction
from domain.services import StatementParser


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
            df = self._load_xlsx_data(file_path)

            # Create statement
            statement = Statement(payment_method=payment_method)

            # Parse transactions based on payment method
            transactions = self._parse_transactions(df, payment_method)

            # Add transactions to statement
            for transaction in transactions:
                statement.add_transaction(transaction)

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
        It is proven to work well with Mercadopago statements.

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
            # Load XLSX file using pandas with openpyxl engine
            df = pd.read_excel(file_path, engine="openpyxl")

            if df.empty:
                raise ValueError(f"No data found in XLSX file: {file_path}")

            return df

        except Exception as e:
            raise ValueError(
                f"Failed to load data from XLSX file {file_path}: {str(e)}"
            ) from e

    def _parse_transactions(
        self, df: pd.DataFrame, payment_method: PaymentMethod
    ) -> list[Transaction]:
        """
        Parse transaction data from XLSX DataFrame based on payment method.

        Currently supports Mercadopago XLSX format with ISO 8601 timestamps.

        Args:
            df: DataFrame containing XLSX data
            payment_method: Detected payment method (should be MERCADOPAGO)

        Returns:
            List of parsed Transaction objects

        Example:
            >>> transactions = parser._parse_transactions(df, PaymentMethod.MERCADOPAGO)
            >>> assert len(transactions) > 0
        """
        transactions = []

        if payment_method == PaymentMethod.MERCADOPAGO:
            transactions = self._parse_mercadopago_transactions(df)

        return transactions

    def _parse_mercadopago_transactions(self, df: pd.DataFrame) -> list[Transaction]:
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
        for _, row in df.iterrows():
            fecha_str = (
                str(row["Fecha de Pago"]).strip()
                if pd.notna(row["Fecha de Pago"])
                else ""
            )
            tipo_operacion = (
                str(row["Tipo de Operación"]).strip()
                if pd.notna(row["Tipo de Operación"])
                else ""
            )
            importe = row["Importe"] if pd.notna(row["Importe"]) else 0

            if fecha_str and tipo_operacion:
                try:
                    # Convert ISO 8601 timestamp to YYYY-MM-DD format
                    # Extract date part from "2025-02-01T17:45:36Z"
                    formatted_date = fecha_str.split("T")[0]

                    # Build transaction using TransactionBuilder
                    transaction = self._transaction_builder.build_from_xls_data(
                        date_str=formatted_date,
                        description=tipo_operacion,
                        amount_str=str(float(importe)),
                        currency=Currency.ARS,
                        payment_method=PaymentMethod.MERCADOPAGO,
                    )
                    transactions.append(transaction)

                except (ValueError, IndexError, TypeError):
                    continue  # Skip invalid rows

        return transactions
