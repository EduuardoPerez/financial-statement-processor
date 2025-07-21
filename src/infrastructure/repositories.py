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

from domain.models import ConsolidatedStatement, Statement
from domain.repositories import FileReader, FileWriter, StatementRepository
from infrastructure.config import PaymentMethodMappingConfig


class ExcelStatementRepository(StatementRepository):
    """Excel-based statement repository implementation."""

    def __init__(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        payment_method_mapping: PaymentMethodMappingConfig | None = None,
    ):
        """
        Initialize the Excel statement repository.

        Args:
            file_reader: File reader implementation for loading raw data
            file_writer: File writer implementation for saving files
            payment_method_mapping: Payment method mapping configuration
        """
        self._file_reader = file_reader
        self._file_writer = file_writer
        self._payment_method_mapping = (
            payment_method_mapping or PaymentMethodMappingConfig()
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
        df = self._statement_to_dataframe(statement)

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

    def _statement_to_dataframe(self, statement: Statement) -> pd.DataFrame:
        """
        Convert Statement object to pandas DataFrame.

        Args:
            statement: Statement to convert

        Returns:
            DataFrame with standardized columns for Excel output

        Note:
            Creates DataFrame with columns: Date, Description, Currency,
            Amount, Payment Method. Date format: YYYY-MM-DD.
            Amount format: Float representation of Decimal
            Uses configured payment method display names if available
        """
        data: list[dict[str, Any]] = []

        for transaction in statement.transactions:
            display_name = self._payment_method_mapping.get_display_name(
                transaction.payment_method
            )
            data.append(
                {
                    "Date": transaction.date.strftime("%Y-%m-%d"),
                    "Description": transaction.description,
                    "Currency": transaction.currency.value,
                    "Amount": float(transaction.amount),
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
        df = self._consolidated_to_dataframe(consolidated)

        # Save as Excel file using pandas with openpyxl engine
        try:
            df.to_excel(
                output_path, index=False, sheet_name="Sheet1", engine="openpyxl"
            )
        except Exception as e:
            raise OSError(
                f"Failed to save consolidated Excel file to {output_path}: {str(e)}"
            ) from e

    def _consolidated_to_dataframe(
        self, consolidated: "ConsolidatedStatement"
    ) -> pd.DataFrame:
        """
        Convert ConsolidatedStatement to DataFrame.

        Args:
            consolidated: ConsolidatedStatement to convert

        Returns:
            DataFrame with all transactions sorted chronologically

        Note:
            Creates DataFrame with columns: Date, Description, Currency,
            Amount, Payment Method. Transactions are already sorted and
            duplicates are already marked in the ConsolidatedStatement.
            Uses configured payment method display names if available
        """
        from typing import Any

        data: list[dict[str, Any]] = []

        for transaction in consolidated.transactions:
            display_name = self._payment_method_mapping.get_display_name(
                transaction.payment_method
            )
            data.append(
                {
                    "Date": transaction.date.strftime("%Y-%m-%d"),
                    "Description": transaction.description,
                    "Currency": transaction.currency.value,
                    "Amount": float(transaction.amount),
                    "Payment Method": display_name,
                }
            )

        return pd.DataFrame(data)
