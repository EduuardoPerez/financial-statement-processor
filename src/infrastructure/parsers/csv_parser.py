"""
CSV statement parser implementation for the Financial Statement Processor.

This module provides a concrete implementation of the StatementParser interface
for processing CSV financial statements using pandas for data extraction.

Classes:
    CSVStatementParser: CSV statement parser using pandas for data extraction
"""

from pathlib import Path
from typing import Any

import pandas as pd

from domain.builders import TransactionBuilder
from domain.models import PaymentMethod, Statement, Transaction
from domain.services import StatementParser

from ._shared import map_currency_es, parse_ddmmyyyy


class CSVStatementParser(StatementParser):
    """
    CSV statement parser using pandas for data extraction.

    This parser handles CSV financial statements by loading structured
    data and creating Statement objects. It serves as a concrete implementation
    of the StatementParser strategy interface.

    The parser is responsible for:
    1. Detecting CSV files by extension (case-insensitive)
    2. Loading structured data from CSV files using pandas
    3. Creating Statement objects with detected payment method
    4. Parsing transactions from CSV data with proper format conversion

    Example:
        >>> detector = SomePaymentMethodDetector()
        >>> parser = CSVStatementParser(detector, transaction_builder)
        >>> can_parse = parser.can_parse(Path("statement.CSV"))
        >>> assert can_parse is True
        >>> statement = parser.parse(Path("statement.csv"))
        >>> assert isinstance(statement, Statement)
    """

    def __init__(self, detector: Any, transaction_builder: TransactionBuilder) -> None:
        """
        Initialize CSV parser with payment method detector and transaction builder.

        Args:
            detector: Payment method detector for identifying bank/card type
                     from CSV content or filename
            transaction_builder: TransactionBuilder for constructing Transaction
                                objects from parsed CSV data
        """
        self._detector = detector
        self._transaction_builder = transaction_builder

    def can_parse(self, file_path: Path) -> bool:
        """
        Determine if this parser can handle the given file.

        Checks if the file has a CSV extension (case-insensitive).

        Args:
            file_path: Path to the file to be parsed

        Returns:
            True if file has .csv extension (case-insensitive),
            False otherwise

        Example:
            >>> parser = CSVStatementParser(detector, transaction_builder)
            >>> assert parser.can_parse(Path("statement.csv")) is True
            >>> assert parser.can_parse(Path("statement.CSV")) is True
            >>> assert parser.can_parse(Path("statement.pdf")) is False
        """
        return file_path.suffix.lower() == ".csv"

    def parse(self, file_path: Path) -> Statement:
        """
        Parse the CSV file and return a Statement object with transactions.

        Loads structured data from the CSV file using pandas and creates a
        Statement object with the detected payment method and parsed transactions.
        Supports both BBVA VISA and Macro VISA CSV formats.

        Args:
            file_path: Path to the CSV file to parse

        Returns:
            Statement object with detected payment method and parsed transactions

        Raises:
            FileNotFoundError: If the input file does not exist
            ValueError: If the file format is invalid or cannot be parsed
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during file processing

        Example:
            >>> parser = CSVStatementParser(detector, transaction_builder)
            >>> statement = parser.parse(Path("statement.csv"))
            >>> assert isinstance(statement, Statement)
            >>> assert len(statement.transactions) > 0
        """
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            # Detect payment method from filename
            payment_method = self._detector.detect_from_filename(file_path)

            # Load CSV data
            df = self._load_csv_data(file_path)

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
                f"Permission denied reading CSV file: {file_path}"
            ) from e
        except Exception as e:
            raise OSError(f"Error processing CSV file {file_path}: {str(e)}") from e

    def get_supported_extensions(self) -> set[str]:
        """
        Return the set of file extensions supported by this parser.

        Returns:
            Set containing '.csv' extension

        Example:
            >>> parser = CSVStatementParser(detector, transaction_builder)
            >>> extensions = parser.get_supported_extensions()
            >>> assert extensions == {'.csv'}
        """
        return {".csv"}

    def _load_csv_data(self, file_path: Path) -> pd.DataFrame:
        """
        Helper method to load structured data from CSV file using pandas.

        This method handles the low-level CSV data loading using pandas
        with semicolon separator which is standard for Argentine bank CSVs.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame containing the CSV data

        Raises:
            ValueError: If CSV file cannot be opened or read
            OSError: If there's an I/O error during loading

        Example:
            >>> parser = CSVStatementParser(detector, transaction_builder)
            >>> df = parser._load_csv_data(Path("statement.csv"))
            >>> assert isinstance(df, pd.DataFrame)
            >>> assert len(df.columns) > 0
        """
        try:
            # Load CSV file using pandas with semicolon separator
            try:
                df = pd.read_csv(file_path, sep=";")
            except UnicodeDecodeError:
                # Argentine bank exports (e.g. BBVA Movimientos) ship in
                # Latin-1, which breaks the default UTF-8 decoding
                df = pd.read_csv(file_path, sep=";", encoding="latin-1")

            if df.empty:
                raise ValueError(f"No data found in CSV file: {file_path}")

            return df

        except Exception as e:
            raise ValueError(
                f"Failed to load data from CSV file {file_path}: {str(e)}"
            ) from e

    def _parse_transactions(
        self, df: pd.DataFrame, payment_method: PaymentMethod
    ) -> list[Transaction]:
        """
        Parse transaction data from CSV DataFrame based on payment method.

        Handles both BBVA VISA and Macro VISA CSV formats with different
        column structures and data layouts.

        Args:
            df: DataFrame containing CSV data
            payment_method: Detected payment method (BBVA VISA or Macro VISA)

        Returns:
            List of parsed Transaction objects

        Example:
            >>> transactions = parser._parse_transactions(df, PaymentMethod.BBVA_VISA)
            >>> assert len(transactions) > 0
        """
        if payment_method in (PaymentMethod.BBVA_VISA, PaymentMethod.MACRO_VISA):
            return self._parse_visa_csv_transactions(df, payment_method)
        return []

    def _parse_visa_csv_transactions(
        self, df: pd.DataFrame, payment_method: PaymentMethod
    ) -> list[Transaction]:
        """
        Parse VISA CSV transactions shared by BBVA and Macro.

        Columns: Fecha (or Fecha Origen), Establecimiento, Moneda, Importe.
        Date format: DD/MM/YYYY. Amount format: 1,234.56 (commas as thousands).
        """
        transactions = []

        for _, row in df.iterrows():
            fecha_str = ""
            if "Fecha Origen" in df.columns and pd.notna(row["Fecha Origen"]):
                fecha_str = str(row["Fecha Origen"]).strip()
            elif "Fecha" in df.columns and pd.notna(row["Fecha"]):
                fecha_str = str(row["Fecha"]).strip()

            establecimiento = (
                str(row["Establecimiento"]).strip()
                if pd.notna(row["Establecimiento"])
                else ""
            )
            moneda = str(row["Moneda"]).strip() if pd.notna(row["Moneda"]) else ""
            importe_str = (
                str(row["Importe"]).strip() if pd.notna(row["Importe"]) else ""
            )

            if not (fecha_str and importe_str and importe_str != "nan"):
                continue

            try:
                formatted_date = parse_ddmmyyyy(fecha_str)
                amount = float(importe_str.replace(",", ""))
                currency = map_currency_es(moneda)

                transaction = self._transaction_builder.build_from_csv_data(
                    date_str=formatted_date,
                    description=establecimiento,
                    amount_str=str(amount),
                    currency=currency,
                    payment_method=payment_method,
                )
                transactions.append(transaction)
            except (ValueError, IndexError):
                continue

        return transactions
