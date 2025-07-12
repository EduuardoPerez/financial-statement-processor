"""
XLS/XLSX statement parser implementation for the Financial Statement Processor.

This module provides a concrete implementation of the StatementParser interface
for processing XLS and XLSX financial statements using pandas for data
extraction.

Classes:
    XLSStatementParser: XLS/XLSX statement parser using pandas for data
                       extraction
"""

from pathlib import Path
from typing import Any

import pandas as pd

from domain.builders import TransactionBuilder
from domain.models import Currency, PaymentMethod, Statement, Transaction
from domain.services import StatementParser


class XLSStatementParser(StatementParser):
    """
    XLS/XLSX statement parser using pandas for data extraction.

    This parser handles XLS and XLSX financial statements by loading structured
    data and creating Statement objects. It serves as a concrete implementation
    of the StatementParser strategy interface.

    The parser is responsible for:
    1. Detecting XLS/XLSX files by extension (case-insensitive)
    2. Loading structured data from Excel files using pandas
    3. Creating Statement objects with detected payment method
    4. Returning statements with transaction data (skeleton: zero transactions)

    Example:
        >>> detector = SomePaymentMethodDetector()
        >>> parser = XLSStatementParser(detector)
        >>> can_parse = parser.can_parse(Path("statement.XLSX"))
        >>> assert can_parse is True
        >>> statement = parser.parse(Path("statement.xls"))
        >>> assert isinstance(statement, Statement)
    """

    def __init__(self, detector: Any, transaction_builder: TransactionBuilder) -> None:
        """
        Initialize XLS parser with payment method detector and transaction builder.

        Args:
            detector: Payment method detector for identifying bank/card type
                     from Excel content or filename
            transaction_builder: TransactionBuilder for constructing Transaction
                                objects from parsed XLS data
        """
        self._detector = detector
        self._transaction_builder = transaction_builder

    def can_parse(self, file_path: Path) -> bool:
        """
        Determine if this parser can handle the given file.

        Checks if the file has an XLS or XLSX extension (case-insensitive).

        Args:
            file_path: Path to the file to be parsed

        Returns:
            True if file has .xls or .xlsx extension (case-insensitive),
            False otherwise

        Example:
            >>> parser = XLSStatementParser(detector)
            >>> assert parser.can_parse(Path("statement.xls")) is True
            >>> assert parser.can_parse(Path("statement.XLSX")) is True
            >>> assert parser.can_parse(Path("statement.pdf")) is False
        """
        return file_path.suffix.lower() == ".xls"

    def parse(self, file_path: Path) -> Statement:
        """
        Parse the XLS/XLSX file and return a Statement object with transactions.

        Loads structured data from the Excel file using pandas and creates a
        Statement object with the detected payment method and parsed transactions.
        Supports both BBVA Account and Macro Account XLS formats.

        Args:
            file_path: Path to the XLS/XLSX file to parse

        Returns:
            Statement object with detected payment method and parsed transactions

        Raises:
            FileNotFoundError: If the input file does not exist
            ValueError: If the file format is invalid or cannot be parsed
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during file processing

        Example:
            >>> parser = XLSStatementParser(detector, transaction_builder)
            >>> statement = parser.parse(Path("statement.xls"))
            >>> assert isinstance(statement, Statement)
            >>> assert len(statement.transactions) > 0
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        try:
            # Detect payment method from filename
            payment_method = self._detector.detect_from_filename(file_path)

            # Load Excel data
            df = self._load_excel_data(file_path)

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
                f"Permission denied reading Excel file: {file_path}"
            ) from e
        except Exception as e:
            raise OSError(f"Error processing Excel file {file_path}: {str(e)}") from e

    def get_supported_extensions(self) -> set[str]:
        """
        Return the set of file extensions supported by this parser.

        Returns:
            Set containing '.xls' and '.xlsx' extensions

        Example:
            >>> parser = XLSStatementParser(detector)
            >>> extensions = parser.get_supported_extensions()
            >>> assert extensions == {'.xls', '.xlsx'}
        """
        return {".xls"}

    def _load_excel_data(self, file_path: Path) -> pd.DataFrame:
        """
        Helper method to load structured data from Excel file using pandas.

        This method handles the low-level Excel data loading using pandas.
        It is proven to work well with Argentine bank statements.

        Args:
            file_path: Path to the Excel file

        Returns:
            DataFrame containing the Excel data

        Raises:
            ValueError: If Excel file cannot be opened or read
            OSError: If there's an I/O error during loading

        Example:
            >>> parser = XLSStatementParser(detector)
            >>> df = parser._load_excel_data(Path("statement.xlsx"))
            >>> assert isinstance(df, pd.DataFrame)
            >>> assert len(df.columns) > 0
        """
        try:
            # Load Excel file using pandas with automatic engine detection
            df = pd.read_excel(file_path)

            if df.empty:
                raise ValueError(f"No data found in Excel file: {file_path}")

            return df

        except Exception as e:
            raise ValueError(
                f"Failed to load data from Excel file {file_path}: {str(e)}"
            ) from e

    def _parse_transactions(
        self, df: pd.DataFrame, payment_method: PaymentMethod
    ) -> list[Transaction]:
        """
        Parse transaction data from Excel DataFrame based on payment method.

        Handles both BBVA Account and Macro Account XLS formats with different
        row structures and data layouts.

        Args:
            df: DataFrame containing Excel data
            payment_method: Detected payment method (BBVA Account or Macro Account)

        Returns:
            List of parsed Transaction objects

        Example:
            >>> transactions = parser._parse_transactions(df, PaymentMethod.BBVA_ACCOUNT)
            >>> assert len(transactions) > 0
        """
        transactions = []

        if payment_method == PaymentMethod.BBVA_ACCOUNT:
            transactions = self._parse_bbva_account_transactions(df)
        elif payment_method == PaymentMethod.MACRO_ACCOUNT:
            transactions = self._parse_macro_account_transactions(df)

        return transactions

    def _parse_bbva_account_transactions(self, df: pd.DataFrame) -> list[Transaction]:
        """
        Parse BBVA Account XLS transactions.

        BBVA Account format:
        - Skip header rows (row 0 is title, row 1 is column headers)
        - Start from row 2 (third row)
        - Columns: Date (0), Description (1), Amount (3)
        - Date format: DD/MM/YYYY
        - Amount format: European (1.234,56)
        """
        transactions = []

        # Skip header rows and get actual data (start from row 2)
        data_rows = df.iloc[2:]

        for _, row in data_rows.iterrows():
            # Check if Date and Amount are not null
            if pd.notna(row.iloc[0]) and pd.notna(row.iloc[3]):
                fecha_str = str(row.iloc[0]).strip()
                concepto_str = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                importe_str = str(row.iloc[3]).strip()

                if fecha_str and importe_str and importe_str != "nan":
                    try:
                        # Convert date from DD/MM/YYYY to YYYY-MM-DD
                        day, month, year = fecha_str.split("/")
                        formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                        # Build transaction using TransactionBuilder
                        transaction = self._transaction_builder.build_from_xls_data(
                            date_str=formatted_date,
                            description=concepto_str,
                            amount_str=importe_str,
                            currency=Currency.ARS,
                            payment_method=PaymentMethod.BBVA_ACCOUNT,
                        )
                        transactions.append(transaction)

                    except (ValueError, IndexError):
                        continue  # Skip invalid rows

        return transactions

    def _parse_macro_account_transactions(self, df: pd.DataFrame) -> list[Transaction]:
        """
        Parse Macro Account XLS transactions.

        Macro Account format:
        - Skip header rows (row 0 is title, row 1 is account number, row 2 is column headers)
        - Start from row 3 (fourth row)
        - Columns: Date (0), Description (2), Amount (3)
        - Date: Already datetime objects
        - Amount: Already numeric format
        """
        transactions = []

        # Skip header rows and get actual data (start from row 3)
        data_rows = df.iloc[3:]

        for _, row in data_rows.iterrows():
            # Check if Date and Amount are not null
            if pd.notna(row.iloc[0]) and pd.notna(row.iloc[3]):
                fecha = row.iloc[0]  # Already a datetime object
                descripcion = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                importe = row.iloc[3]  # Already a number

                if fecha and pd.notna(importe):
                    try:
                        # Convert datetime to YYYY-MM-DD format
                        formatted_date = fecha.strftime("%Y-%m-%d")

                        # Build transaction using TransactionBuilder
                        transaction = self._transaction_builder.build_from_xls_data(
                            date_str=formatted_date,
                            description=descripcion,
                            amount_str=str(float(importe)),
                            currency=Currency.ARS,
                            payment_method=PaymentMethod.MACRO_ACCOUNT,
                        )
                        transactions.append(transaction)

                    except (ValueError, AttributeError):
                        continue  # Skip invalid rows

        return transactions
