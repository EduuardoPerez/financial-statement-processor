"""
Infrastructure implementations of repository abstractions.

This module provides concrete implementations of the repository interfaces
defined in the domain layer, specifically for Excel-based statement persistence.

Classes:
    ExcelStatementRepository: Excel-based statement repository implementation
"""

from pathlib import Path
from typing import Any

import pandas as pd

from domain.models import ConsolidatedStatement, Statement, Transaction
from domain.repositories import FileReader, FileWriter, StatementRepository
from infrastructure.config import (
    AmountSignInversionConfig,
    OutputConfig,
    PaymentMethodMappingConfig,
)


class _PathFileReader:
    def read(self, path: Path) -> bytes:
        return path.read_bytes()

    def exists(self, path: Path) -> bool:
        return path.exists()


class _PathFileWriter:
    def write(self, path: Path, content: bytes) -> None:
        path.write_bytes(content)

    def ensure_directory(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)


class ExcelStatementRepository(StatementRepository):
    """Excel-based statement repository implementation."""

    def __init__(
        self,
        file_reader: FileReader | None = None,
        file_writer: FileWriter | None = None,
        payment_method_mapping: PaymentMethodMappingConfig | None = None,
        output_config: OutputConfig | None = None,
        amount_sign_inversion: AmountSignInversionConfig | None = None,
    ):
        """
        Initialize the Excel statement repository.

        Args:
            file_reader: File reader implementation; defaults to Path-based reader
            file_writer: File writer implementation; defaults to Path-based writer
            payment_method_mapping: Payment method mapping configuration
            output_config: Output configuration including decimal separator
            amount_sign_inversion: Amount sign inversion configuration
        """
        self._file_reader: FileReader = file_reader or _PathFileReader()
        self._file_writer: FileWriter = file_writer or _PathFileWriter()
        self._payment_method_mapping = (
            payment_method_mapping or PaymentMethodMappingConfig()
        )
        self._output_config = output_config or OutputConfig()
        self._amount_sign_inversion = (
            amount_sign_inversion or AmountSignInversionConfig()
        )

    def save_statement(self, statement: Statement, output_path: Path) -> None:
        """
        Save statement to Excel file at specified path.

        Args:
            statement: The statement to save
            output_path: Path where the Excel file should be saved

        Raises:
            ValueError: If the statement is invalid
            OSError: If there's an error writing the file
        """
        if not statement.transactions:
            raise ValueError("Cannot save statement with no transactions")

        # Ensure output directory exists
        self._file_writer.ensure_directory(output_path.parent)

        # Convert statement to DataFrame
        df = self._transactions_to_dataframe(statement.transactions)

        # Save as Excel file using pandas with openpyxl engine
        try:
            df.to_excel(
                output_path, index=False, sheet_name="Sheet1", engine="openpyxl"
            )
        except Exception as e:
            raise OSError(
                f"Failed to save Excel file to {output_path}: {str(e)}"
            ) from e

    def load_raw_data(self, input_path: Path) -> bytes:
        """
        Load raw data from input file.

        Args:
            input_path: Path to the input file

        Returns:
            Raw file data as bytes

        Raises:
            FileNotFoundError: If the input file does not exist
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during reading
        """
        if not self._file_reader.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        try:
            raw_data: bytes = self._file_reader.read(input_path)
            return raw_data
        except PermissionError as e:
            raise PermissionError(f"Permission denied reading {input_path}") from e
        except Exception as e:
            raise OSError(f"Error reading file {input_path}: {str(e)}") from e

    def _transactions_to_dataframe(
        self, transactions: list[Transaction]
    ) -> pd.DataFrame:
        """
        Convert a list of Transaction objects to a standardized DataFrame.

        Columns: Date (YYYY-MM-DD), Description, Currency, Amount (string with
        configured decimal separator), Payment Method (using display name
        mapping). Applies sign inversion per payment method.
        """
        data: list[dict[str, Any]] = []

        for transaction in transactions:
            display_name = self._payment_method_mapping.get_display_name(
                transaction.payment_method
            )
            amount = transaction.amount
            if self._amount_sign_inversion.should_invert(transaction.payment_method):
                amount = -amount
            amount_str = str(float(amount))
            if self._output_config.decimal_separator != ".":
                amount_str = amount_str.replace(
                    ".", self._output_config.decimal_separator
                )

            data.append(
                {
                    "Date": transaction.date.strftime("%Y-%m-%d"),
                    "Description": transaction.description,
                    "Currency": transaction.currency.value,
                    "Amount": amount_str,
                    "Payment Method": display_name,
                }
            )

        return pd.DataFrame(data)

    def save_consolidated_statement(
        self, consolidated: "ConsolidatedStatement", output_path: Path
    ) -> None:
        """
        Save consolidated statement to Excel file.

        Args:
            consolidated: Consolidated statement to save
            output_path: Path for output Excel file

        Excel Structure:
        - All transactions in single sheet
        - Columns: Date, Description, Currency, Amount, Payment Method
        - Sorted by date ascending
        - Duplicates marked with "DUPLICATED: " prefix

        Raises:
            ValueError: If the consolidated statement is invalid
            OSError: If there's an error writing the file
        """
        if not consolidated.transactions:
            raise ValueError("Cannot save consolidated statement with no transactions")

        # Ensure output directory exists
        self._file_writer.ensure_directory(output_path.parent)

        # Convert consolidated statement to DataFrame
        df = self._transactions_to_dataframe(consolidated.transactions)

        # Save as Excel file using pandas with openpyxl engine
        try:
            df.to_excel(
                output_path, index=False, sheet_name="Sheet1", engine="openpyxl"
            )
        except Exception as e:
            raise OSError(
                f"Failed to save consolidated Excel file to {output_path}: {str(e)}"
            ) from e
