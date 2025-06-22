"""
Factory abstractions for the Financial Statement Processor.

This module defines factory interfaces for creating parser instances in a
pluggable manner. The factory pattern enables dynamic parser selection
based on file characteristics while maintaining clean architecture principles.

Classes:
    ParserFactory: Factory for creating appropriate statement parsers
"""

from pathlib import Path

from .services import StatementParser

__all__ = [
    "ParserFactory",
]


class ParserFactory:
    """
    Factory for creating appropriate statement parsers.

    This factory manages a registry of StatementParser implementations and
    provides methods to dynamically select the appropriate parser for a given
    file. It implements the Factory Pattern to decouple parser creation from
    client code and enables the Strategy Pattern for pluggable parsing logic.

    The factory maintains a list of registered parsers and uses their
    can_parse() method to determine which parser can handle a specific file.
    This design follows the Open/Closed Principle - new parsers can be added
    without modifying existing code.

    Attributes:
        _parsers: List of registered StatementParser instances

    Example:
        >>> factory = ParserFactory()
        >>> pdf_parser = PDFStatementParser(detector)
        >>> xls_parser = XLSStatementParser(detector)
        >>>
        >>> factory.register_parser(pdf_parser)
        >>> factory.register_parser(xls_parser)
        >>>
        >>> parser = factory.create_parser(Path("statement.pdf"))
        >>> statement = parser.parse(Path("statement.pdf"))
    """

    def __init__(self) -> None:
        """Initialize factory with empty parser registry."""
        self._parsers: list[StatementParser] = []

    def register_parser(self, parser: StatementParser) -> None:
        """
        Register a new parser strategy.

        Adds a StatementParser implementation to the factory's registry.
        The parser will be considered when creating parsers for files.
        Parsers are checked in registration order, so more specific
        parsers should be registered before more general ones.

        Args:
            parser: StatementParser implementation to register

        Raises:
            TypeError: If parser is not a StatementParser instance

        Example:
            >>> factory = ParserFactory()
            >>> pdf_parser = PDFStatementParser(detector)
            >>> factory.register_parser(pdf_parser)
            >>> assert len(factory._parsers) == 1
        """
        if not isinstance(parser, StatementParser):
            parser_type = type(parser).__name__
            raise TypeError(f"Expected StatementParser, got {parser_type}")

        self._parsers.append(parser)

    def create_parser(self, file_path: Path) -> StatementParser:
        """
        Create appropriate parser for the given file.

        Iterates through registered parsers and returns the first one
        that can handle the specified file. Uses each parser's can_parse()
        method to determine compatibility.

        Args:
            file_path: Path to the file that needs to be parsed

        Returns:
            StatementParser instance capable of parsing the file

        Raises:
            ValueError: If no registered parser can handle the file
            TypeError: If file_path is not a Path instance

        Example:
            >>> factory = ParserFactory()
            >>> factory.register_parser(PDFStatementParser(detector))
            >>> parser = factory.create_parser(Path("statement.pdf"))
            >>> assert isinstance(parser, PDFStatementParser)
        """
        if not isinstance(file_path, Path):
            raise TypeError(f"Expected Path, got {type(file_path).__name__}")

        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser

        # No parser found - create descriptive error message
        supported_extensions = self.get_supported_extensions()
        file_extension = file_path.suffix.lower()

        if supported_extensions:
            supported_list = ", ".join(sorted(supported_extensions))
            error_msg = (
                f"No parser available for file: {file_path}. "
                f"File extension '{file_extension}' is not supported. "
                f"Supported extensions: {supported_list}"
            )
        else:
            error_msg = (
                f"No parser available for file: {file_path}. "
                f"No parsers are registered in the factory."
            )

        raise ValueError(error_msg)

    def get_supported_extensions(self) -> set[str]:
        """
        Get all supported file extensions from registered parsers.

        Aggregates the supported extensions from all registered parsers
        into a single set. This provides a comprehensive view of what
        file types the factory can handle.

        Returns:
            Set of supported file extensions (e.g., {'.pdf', '.xls', '.xlsx'})

        Example:
            >>> factory = ParserFactory()
            >>> pdf_parser = PDFStatementParser(detector)  # .pdf
            >>> xls_parser = XLSStatementParser(detector)  # .xls, .xlsx
            >>> factory.register_parser(pdf_parser)
            >>> factory.register_parser(xls_parser)
            >>> extensions = factory.get_supported_extensions()
            >>> assert extensions == {'.pdf', '.xls', '.xlsx'}
        """
        extensions: set[str] = set()

        for parser in self._parsers:
            extensions.update(parser.get_supported_extensions())

        return extensions

    def get_registered_parsers(self) -> list[StatementParser]:
        """
        Get a copy of all registered parsers.

        Returns a copy of the internal parser list to prevent external
        modification while allowing inspection of registered parsers.

        Returns:
            List of registered StatementParser instances

        Example:
            >>> factory = ParserFactory()
            >>> factory.register_parser(PDFStatementParser(detector))
            >>> parsers = factory.get_registered_parsers()
            >>> assert len(parsers) == 1
            >>> assert isinstance(parsers[0], PDFStatementParser)
        """
        return self._parsers.copy()

    def clear_parsers(self) -> None:
        """
        Clear all registered parsers.

        Removes all parsers from the factory registry. Useful for
        testing or reconfiguring the factory with a different set
        of parsers.

        Example:
            >>> factory = ParserFactory()
            >>> factory.register_parser(PDFStatementParser(detector))
            >>> assert len(factory.get_registered_parsers()) == 1
            >>> factory.clear_parsers()
            >>> assert len(factory.get_registered_parsers()) == 0
        """
        self._parsers.clear()
