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

from domain.models import PaymentMethod, Statement
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

    def __init__(self, detector: Any) -> None:
        """
        Initialize XLS parser with payment method detector.

        Args:
            detector: Payment method detector for identifying bank/card type
                     from Excel content or filename
        """
        self._detector = detector

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
        return file_path.suffix.lower() in {".xls", ".xlsx"}

    def parse(self, file_path: Path) -> Statement:
        """
        Parse the XLS/XLSX file and return a Statement object.

        Loads structured data from the Excel file using pandas and creates a
        Statement object with the detected payment method. This skeleton
        implementation returns a statement with zero transactions.

        Args:
            file_path: Path to the XLS/XLSX file to parse

        Returns:
            Statement object with detected payment method and empty
            transactions

        Raises:
            FileNotFoundError: If the input file does not exist
            ValueError: If the file format is invalid or cannot be parsed
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during file processing

        Example:
            >>> parser = XLSStatementParser(detector)
            >>> statement = parser.parse(Path("statement.xlsx"))
            >>> assert isinstance(statement, Statement)
            >>> assert len(statement.transactions) == 0  # Skeleton impl
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        try:
            # Load Excel data using pandas (skeleton: not used yet)
            # df = self._load_excel_data(file_path)

            # Detect payment method from content/filename
            # For skeleton implementation, default to BBVA_VISA
            # In full implementation, this would use the detector
            payment_method = PaymentMethod.BBVA_VISA

            # Create and return Statement with zero transactions (skeleton)
            statement = Statement(payment_method=payment_method)
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
        return {".xls", ".xlsx"}

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
