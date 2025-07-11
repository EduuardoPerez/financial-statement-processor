"""
Service abstractions for the Financial Statement Processor.

This module defines abstract service interfaces that form the core business
logic contracts in our hexagonal architecture. These abstractions enable
the Strategy Pattern for different parsing implementations.

Classes:
    StatementParser: Abstract strategy for parsing different statement formats
"""

from abc import ABC, abstractmethod
from pathlib import Path

from .models import Statement


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
