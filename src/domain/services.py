"""
Service abstractions for the Financial Statement Processor.

This module defines abstract service interfaces that form the core business
logic contracts in our hexagonal architecture. These abstractions enable
the Strategy Pattern for different parsing implementations.

Classes:
    StatementParser: Abstract strategy for parsing different statement formats
    BalanceExtractor: Abstract service for extracting reported balances
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from pathlib import Path

from .models import PaymentMethod, Statement, Transaction


class StatementParser(ABC):
    """
    Abstract strategy for parsing different statement formats.

    This abstract base class defines the contract that all concrete statement
    parsers must implement. It enables the Strategy Pattern for handling
    different file formats (PDF, XLS, CSV, XLSX) in a pluggable manner.

    The parser is responsible for:
    1. Determining if it can handle a specific file format
    2. Parsing the file and extracting transaction data
    3. Returning a properly constructed Statement domain object

    Example:
        >>> class PDFStatementParser(StatementParser):
        ...     def can_parse(self, file_path: Path) -> bool:
        ...         return file_path.suffix.lower() == '.pdf'
        ...
        ...     def parse(self, file_path: Path) -> Statement:
        ...         # Implementation details...
        ...         return statement
        ...
        ...     def get_supported_extensions(self) -> set[str]:
        ...         return {'.pdf'}
        >>>
        >>> parser = PDFStatementParser()
        >>> assert issubclass(PDFStatementParser, StatementParser)
    """

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        Determine if this parser can handle the given file.

        This method should examine the file path, extension, or content
        to determine if this specific parser implementation can process
        the file format.

        Args:
            file_path: Path to the file to be parsed

        Returns:
            True if this parser can handle the file, False otherwise

        Example:
            >>> parser = SomeConcreteParser()
            >>> can_handle = parser.can_parse(Path("statement.pdf"))
            >>> print(f"Can parse: {can_handle}")
        """
        ...

    @abstractmethod
    def parse(self, file_path: Path) -> Statement:
        """
        Parse the file and return a Statement object.

        This method performs the actual parsing of the financial statement
        file, extracting transaction data and constructing a properly
        validated Statement domain object with all transactions.

        Args:
            file_path: Path to the file to parse

        Returns:
            Statement object containing all parsed transactions and metadata

        Raises:
            FileNotFoundError: If the input file does not exist
            ValueError: If the file format is invalid or cannot be parsed
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during file processing

        Example:
            >>> parser = SomeConcreteParser()
            >>> statement = parser.parse(Path("statement.pdf"))
            >>> print(f"Parsed {len(statement.transactions)} transactions")
        """
        ...

    @abstractmethod
    def get_supported_extensions(self) -> set[str]:
        """
        Return the set of file extensions supported by this parser.

        This method returns all file extensions that this parser can handle.
        Extensions should be lowercase and include the leading dot.

        Returns:
            Set of supported file extensions (e.g., {'.pdf', '.xls'})

        Example:
            >>> parser = SomeConcreteParser()
            >>> extensions = parser.get_supported_extensions()
            >>> print(f"Supported: {', '.join(sorted(extensions))}")
        """
        ...

    def parse_with_content(self, file_path: Path) -> tuple[Statement, str]:
        """
        Parse the file and return Statement with raw content.

        This method is used for enhanced validation that needs access to
        the raw file content for balance extraction. Default implementation
        calls parse() and returns empty string for content.

        Args:
            file_path: Path to the file to parse

        Returns:
            Tuple of (Statement object, raw content string)

        Raises:
            FileNotFoundError: If the input file does not exist
            ValueError: If the file format is invalid or cannot be parsed
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during file processing

        Example:
            >>> parser = SomeConcreteParser()
            >>> stmt, content = parser.parse_with_content(Path("stmt.pdf"))
            >>> print(f"Parsed {len(stmt.transactions)} transactions")
            >>> print(f"Raw content length: {len(content)}")
        """
        # Default implementation for backward compatibility
        statement = self.parse(file_path)
        return statement, ""


class BalanceExtractor(ABC):
    """Abstract service for extracting reported balances from statements."""

    @abstractmethod
    def extract_balance(
        self,
        content: str,
        payment_method: PaymentMethod,
    ) -> dict[str, Decimal]:
        """
        Extract reported balance from statement content.

        Args:
            content: Raw statement content
            payment_method: Payment method for extraction strategy

        Returns:
            Dictionary with 'ars' and 'usd' balance amounts

        Raises:
            ValueError: If content is invalid or extraction fails
        """
        pass

    @abstractmethod
    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """
        Check if extractor supports the payment method.

        Args:
            payment_method: Payment method to check

        Returns:
            True if this extractor can handle the payment method
        """
        pass


class DuplicateDetector:
    """
    Service for detecting and marking duplicate transactions.

    A transaction is considered duplicate if it has the same date and amount
    as another transaction, regardless of payment method or description.
    Duplicates are marked with configurable prefix in the description.
    """

    def __init__(self, duplicate_prefix: str = "DUPLICATED"):
        """
        Initialize the duplicate detector.

        Args:
            duplicate_prefix: Prefix to use for marking duplicate transactions
        """
        self.duplicate_prefix = duplicate_prefix

    def mark_duplicates(
        self, transactions: list[Transaction]
    ) -> tuple[list[Transaction], int]:
        """
        Mark duplicate transactions with 'DUPLICATED: ' prefix.

        Args:
            transactions: List of transactions to process

        Returns:
            Tuple of (marked_transactions, duplicate_count)

        Algorithm:
            1. Group transactions by (date, amount) tuple
            2. For groups with multiple transactions, mark all but first as
               duplicated
            3. Return new transaction list with modified descriptions and count
        """
        from collections import defaultdict

        if not transactions:
            return transactions, 0

        # Group transactions by (date, amount)
        groups = defaultdict(list)
        for transaction in transactions:
            key = self._create_duplicate_key(transaction)
            groups[key].append(transaction)

        # Mark duplicates (all but first in each group)
        result = []
        duplicate_count = 0

        for group in groups.values():
            # First occurrence - keep original
            result.append(group[0])

            # Mark subsequent as duplicates
            for duplicate in group[1:]:
                marked = self._mark_as_duplicate(duplicate)
                result.append(marked)
                duplicate_count += 1

        return result, duplicate_count

    def _create_duplicate_key(self, transaction: Transaction) -> tuple:
        """Create key for duplicate detection (date, absolute_amount)."""
        return (transaction.date, abs(transaction.amount))

    def _mark_as_duplicate(self, transaction: Transaction) -> Transaction:
        """Create new transaction with configurable prefix."""
        new_description = f"{self.duplicate_prefix}: {transaction.description}"

        return Transaction(
            date=transaction.date,
            description=new_description,
            amount=transaction.amount,
            currency=transaction.currency,
            payment_method=transaction.payment_method,
            reference=transaction.reference,
        )
