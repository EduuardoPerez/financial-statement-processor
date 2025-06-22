"""
Infrastructure factory implementations for the Financial Statement Processor.

This module provides concrete factory implementations that auto-register
standard parsers for common use cases. These factories build upon the
abstract factory pattern defined in the domain layer.

Classes:
    DefaultParserFactory: Factory pre-configured with PDF and XLS parsers
"""

from typing import Any

from domain.builders import TransactionBuilder
from domain.factories import ParserFactory
from domain.utils import AmountParser, DateConverter

from .parsers.pdf_parser import PDFStatementParser
from .parsers.xls_parser import XLSStatementParser

__all__ = [
    "DefaultParserFactory",
]


class DefaultParserFactory(ParserFactory):
    """
    Default factory with standard PDF and XLS parsers pre-registered.

    This factory provides a convenient, pre-configured implementation that
    automatically registers the most commonly used parsers for PDF and
    XLS/XLSX financial statements. It extends the base ParserFactory with
    concrete parser implementations from the infrastructure layer.

    The factory auto-registers:
    - PDFStatementParser: Handles .pdf files using pdfplumber
    - XLSStatementParser: Handles .xls and .xlsx files using pandas

    This follows the Factory Pattern by providing a concrete implementation
    that encapsulates the creation and registration of standard parsers,
    while still allowing additional parsers to be registered if needed.

    Example:
        >>> detector = SomePaymentMethodDetector()
        >>> factory = DefaultParserFactory(detector)
        >>> extensions = factory.get_supported_extensions()
        >>> assert extensions == {'.pdf', '.xls', '.xlsx'}
        >>>
        >>> parser = factory.create_parser(Path("statement.pdf"))
        >>> assert isinstance(parser, PDFStatementParser)
    """

    def __init__(self, detector: Any) -> None:
        """
        Initialize factory with detector and auto-register standard parsers.

        Creates a new factory instance and automatically registers the
        standard PDF and XLS parsers with the provided detector. The
        detector is injected into each parser for payment method detection.
        Also creates and injects TransactionBuilder for PDF parsing.

        Args:
            detector: Payment method detector to be injected into parsers
                     for identifying bank/card types from file content
                     or filenames

        Example:
            >>> detector = PaymentMethodDetector()
            >>> factory = DefaultParserFactory(detector)
            >>> assert len(factory.get_registered_parsers()) == 2
        """
        super().__init__()

        # Create utility dependencies for TransactionBuilder
        date_converter = DateConverter()
        amount_parser = AmountParser()
        transaction_builder = TransactionBuilder(date_converter, amount_parser)

        # Auto-register standard parsers with injected dependencies
        self.register_parser(PDFStatementParser(detector, transaction_builder))
        self.register_parser(XLSStatementParser(detector))
