"""
Builder classes for constructing domain objects.

This module provides builder classes that follow the Single Responsibility
Principle, focusing on the construction of complex domain objects with
proper validation and dependency injection for the clean architecture
transformation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import (
    Balance,
    Currency,
    PaymentMethod,
    Statement,
    Transaction,
)
from .utils import AmountParser, DateConverter


class TransactionBuilder:
    """
    Builder for constructing Transaction objects from parsed components.

    This class follows the Single Responsibility Principle by focusing solely
    on Transaction object construction. It uses injected DateConverter and
    AmountParser utilities to handle the parsing of date and amount components,
    then constructs properly validated Transaction objects.

    The builder is designed for use in PDF parsing workflows where transaction
    components are extracted from text lines and need to be converted into
    domain objects.
    """

    def __init__(
        self, date_converter: DateConverter, amount_parser: AmountParser
    ) -> None:
        """
        Initialize TransactionBuilder with injected dependencies.

        Args:
            date_converter: DateConverter instance for parsing date strings
            amount_parser: AmountParser instance for parsing European format
                amounts

        Example:
            >>> from domain.utils import DateConverter, AmountParser
            >>> builder = TransactionBuilder(
            ...     DateConverter(), AmountParser()
            ... )
        """
        self._date_converter = date_converter
        self._amount_parser = amount_parser

    def build_from_pdf_line(
        self,
        date_str: str,
        description: str,
        amount_str: str,
        currency: Currency,
        payment_method: PaymentMethod,
    ) -> Transaction:
        """
        Build Transaction object from PDF line components.

        Takes the individual components extracted from a PDF transaction line
        and constructs a properly validated Transaction domain object using
        the injected utility parsers.

        Args:
            date_str: Date string in DD.MM.YY format (e.g., "05.06.25")
            description: Transaction description text
            amount_str: Amount string in European format (e.g., "1.234,56")
            currency: Currency enum value (ARS or USD)
            payment_method: PaymentMethod enum value

        Returns:
            Transaction: Properly constructed and validated Transaction object

        Raises:
            ValueError: If any component cannot be parsed or validation fails

        Example:
            >>> from domain.models import Currency, PaymentMethod
            >>> transaction = builder.build_from_pdf_line(
            ...     date_str="05.06.25",
            ...     description="COMPRA EN COMERCIO",
            ...     amount_str="1.234,56",
            ...     currency=Currency.ARS,
            ...     payment_method=PaymentMethod.BBVA_VISA
            ... )
            >>> transaction.date.year
            2025
            >>> transaction.amount
            Decimal('1234.56')
        """
        # Import here to avoid circular imports
        from .models import Transaction

        if not date_str or not date_str.strip():
            raise ValueError("Date string cannot be empty")

        if not description or not description.strip():
            raise ValueError("Description cannot be empty")

        if not amount_str or not amount_str.strip():
            raise ValueError("Amount string cannot be empty")

        try:
            # Use injected DateConverter to parse date
            date_clean = date_str.strip()
            parsed_date = self._date_converter.convert_dd_mm_yy(date_clean)

            # Use injected AmountParser to parse amount
            parsed_amount = self._amount_parser.parse_european_format(
                amount_str.strip()
            )

            # Clean description
            clean_description = description.strip()

            # Construct Transaction using domain model
            transaction = Transaction(
                date=parsed_date,
                description=clean_description,
                amount=parsed_amount,
                currency=currency,
                payment_method=payment_method,
            )

            return transaction

        except ValueError as e:
            # Re-raise with context about which component failed
            msg = f"Failed to build transaction from PDF line components: {e}"
            raise ValueError(msg) from e
        except Exception as e:
            # Handle unexpected errors
            msg = f"Unexpected error building transaction: {str(e)}"
            raise ValueError(msg) from e


class StatementBuilder:
    """
    Fluent builder for constructing Statement objects.

    This class provides a fluent interface for building Statement objects
    with method chaining. It ensures that the builder-produced statement
    equals the result of direct constructor usage while providing a more
    readable and flexible construction API.

    The builder follows the established patterns in the codebase and
    integrates seamlessly with existing domain models.
    """

    def __init__(self) -> None:
        """
        Initialize StatementBuilder with empty state.

        Example:
            >>> builder = StatementBuilder()
            >>> statement = (builder
            ...     .with_payment_method(PaymentMethod.BBVA_VISA)
            ...     .add_transaction(transaction)
            ...     .build())
        """
        self._payment_method: PaymentMethod | None = None
        self._transactions: list[Transaction] = []
        self._reported_balance: Balance | None = None

    def with_payment_method(self, payment_method: PaymentMethod) -> StatementBuilder:
        """
        Set the payment method for the statement.

        Args:
            payment_method: PaymentMethod enum value

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_payment_method(PaymentMethod.BBVA_VISA)
        """
        self._payment_method = payment_method
        return self

    def add_transaction(self, transaction: Transaction) -> StatementBuilder:
        """
        Add a single transaction to the statement.

        Args:
            transaction: Transaction object to add

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_transaction(transaction)
        """
        self._transactions.append(transaction)
        return self

    def add_transactions(self, transactions: list[Transaction]) -> StatementBuilder:
        """
        Add multiple transactions to the statement.

        Args:
            transactions: List of Transaction objects to add

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_transactions([transaction1, transaction2])
        """
        self._transactions.extend(transactions)
        return self

    def with_reported_balance(self, balance: Balance) -> StatementBuilder:
        """
        Set the reported balance for the statement.

        Args:
            balance: Balance object with reported amounts

        Returns:
            Self for method chaining

        Example:
            >>> from decimal import Decimal
            >>> balance = Balance(Decimal("1000.00"), Decimal("100.00"))
            >>> builder.with_reported_balance(balance)
        """
        self._reported_balance = balance
        return self

    def build(self) -> Statement:
        """
        Build the final Statement object with validation.

        Creates a Statement using the same constructor as direct instantiation,
        ensuring that builder-produced statements equal direct constructor
        results.

        Returns:
            Statement: Properly constructed and validated Statement object

        Raises:
            ValueError: If payment method is not set or other validation fails

        Example:
            >>> statement = builder.build()
            >>> len(statement.transactions)
            2
        """
        # Import here to avoid circular imports
        from .models import Statement

        if self._payment_method is None:
            raise ValueError("Payment method is required to build Statement")

        # Create statement using exact same constructor as direct usage
        # This ensures builder-produced statement equals direct constructor result
        statement = Statement(
            payment_method=self._payment_method,
            transactions=self._transactions.copy(),  # Copy to prevent mutation
            reported_balance=self._reported_balance,
        )

        return statement

    def reset(self) -> StatementBuilder:
        """
        Reset builder state for reuse.

        Clears all previously set values, allowing the builder to be reused
        for constructing multiple statements.

        Returns:
            Self for method chaining

        Example:
            >>> builder.reset().with_payment_method(PaymentMethod.MACRO_VISA)
        """
        self._payment_method = None
        self._transactions.clear()
        self._reported_balance = None
        return self


@dataclass(frozen=True)
class ProcessingReport:
    """
    Immutable report of batch processing results.

    This dataclass contains comprehensive information about a batch processing
    operation, including successful and failed files, success rates, and
    processing metrics. It follows the established patterns in the codebase
    for immutable value objects.
    """

    successful_files: list[Path]
    failed_files: list[tuple[Path, str]]
    total_processing_time: float = 0.0
    total_transactions: int = 0

    @property
    def success_rate(self) -> float:
        """
        Calculate the success rate as a float between 0.0 and 1.0.

        Returns:
            float: Success rate (successful files / total files)
                  Returns 0.0 if no files were processed

        Example:
            >>> report = ProcessingReport([Path("file1.pdf")], [])
            >>> report.success_rate
            1.0
            >>> report = ProcessingReport([Path("file1.pdf")],
            ...                          [(Path("file2.pdf"), "error")])
            >>> report.success_rate
            0.5
        """
        total_files = len(self.successful_files) + len(self.failed_files)
        if total_files == 0:
            return 0.0
        return len(self.successful_files) / total_files

    @property
    def total_files(self) -> int:
        """
        Get total number of files processed (successful + failed).

        Returns:
            int: Total number of files processed
        """
        return len(self.successful_files) + len(self.failed_files)

    def print_summary(self) -> None:
        """
        Print formatted summary of processing results.

        Displays a comprehensive summary including success rate, file counts,
        processing time, and transaction totals in a readable format.
        """
        print("\n" + "=" * 60)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"✅ Successful files: {len(self.successful_files)}")
        print(f"❌ Failed files: {len(self.failed_files)}")
        print(f"📊 Success rate: {self.success_rate:.1%}")
        print(f"📈 Total transactions: {self.total_transactions}")
        print(f"⏱️  Processing time: {self.total_processing_time:.2f}s")

        if self.failed_files:
            print("\n❌ Failed Files:")
            for file_path, error in self.failed_files:
                print(f"   {file_path.name}: {error}")


class ProcessingReportBuilder:
    """
    Builder for constructing ProcessingReport objects.

    This class provides a fluent interface for building ProcessingReport
    objects with method chaining. It tracks successful and failed file
    processing operations and automatically calculates success rates.

    The builder follows the established patterns in the codebase and
    integrates seamlessly with existing domain models.
    """

    def __init__(self) -> None:
        """
        Initialize ProcessingReportBuilder with empty state.

        Example:
            >>> builder = ProcessingReportBuilder()
            >>> report = (builder
            ...     .add_success(Path("file1.pdf"), 45)
            ...     .add_failure(Path("file2.pdf"), "Parse error")
            ...     .build())
            >>> report.success_rate
            0.5
        """
        self._successful_files: list[Path] = []
        self._failed_files: list[tuple[Path, str]] = []
        self._total_processing_time: float = 0.0
        self._total_transactions: int = 0

    def add_success(
        self, file_path: Path, transaction_count: int = 0
    ) -> ProcessingReportBuilder:
        """
        Add a successfully processed file to the report.

        Args:
            file_path: Path to the successfully processed file
            transaction_count: Number of transactions processed from this file

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_success(Path("statement.pdf"), 45)
        """
        self._successful_files.append(file_path)
        self._total_transactions += transaction_count
        return self

    def add_failure(
        self, file_path: Path, error_message: str
    ) -> ProcessingReportBuilder:
        """
        Add a failed file to the report.

        Args:
            file_path: Path to the file that failed processing
            error_message: Description of the error that occurred

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_failure(Path("bad.pdf"), "File corrupted")
        """
        self._failed_files.append((file_path, error_message))
        return self

    def with_processing_time(self, time_seconds: float) -> ProcessingReportBuilder:
        """
        Set the total processing time for the batch operation.

        Args:
            time_seconds: Total processing time in seconds

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_processing_time(45.2)
        """
        self._total_processing_time = time_seconds
        return self

    def build(self) -> ProcessingReport:
        """
        Build the final ProcessingReport object.

        Creates a ProcessingReport with all accumulated data and automatically
        calculated success rate.

        Returns:
            ProcessingReport: Immutable report with processing results

        Example:
            >>> report = builder.build()
            >>> report.success_rate
            0.5
        """
        return ProcessingReport(
            successful_files=self._successful_files.copy(),
            failed_files=self._failed_files.copy(),
            total_processing_time=self._total_processing_time,
            total_transactions=self._total_transactions,
        )

    def reset(self) -> ProcessingReportBuilder:
        """
        Reset builder state for reuse.

        Clears all previously accumulated data, allowing the builder to be
        reused for constructing multiple reports.

        Returns:
            Self for method chaining

        Example:
            >>> builder.reset().add_success(Path("new_file.pdf"))
        """
        self._successful_files.clear()
        self._failed_files.clear()
        self._total_processing_time = 0.0
        self._total_transactions = 0
        return self
