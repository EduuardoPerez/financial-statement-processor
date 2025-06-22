"""
PDF statement parser implementation for the Financial Statement Processor.

This module provides a concrete implementation of the StatementParser interface
for processing PDF financial statements using pdfplumber for text extraction.

Classes:
    PDFStatementParser: PDF statement parser using pdfplumber for text extraction
"""

from pathlib import Path
from typing import Any

import pdfplumber

from src.domain.models import PaymentMethod, Statement
from src.domain.services import StatementParser

__all__ = [
    "PDFStatementParser",
]


class PDFStatementParser(StatementParser):
    """
    PDF statement parser using pdfplumber for text extraction.

    This parser handles PDF financial statements by extracting raw text
    and creating Statement objects. It serves as a concrete implementation
    of the StatementParser strategy interface.

    The parser is responsible for:
    1. Detecting PDF files by extension (case-insensitive)
    2. Extracting raw text from PDF using pdfplumber
    3. Creating Statement objects with detected payment method
    4. Returning statements with transaction data (skeleton: zero transactions)

    Example:
        >>> detector = SomePaymentMethodDetector()
        >>> parser = PDFStatementParser(detector)
        >>> can_parse = parser.can_parse(Path("statement.PDF"))
        >>> assert can_parse is True
        >>> statement = parser.parse(Path("statement.pdf"))
        >>> assert isinstance(statement, Statement)
    """

    def __init__(self, detector: Any) -> None:
        """
        Initialize PDF parser with payment method detector.

        Args:
            detector: Payment method detector for identifying bank/card type
                     from PDF content or filename
        """
        self._detector = detector

    def can_parse(self, file_path: Path) -> bool:
        """
        Determine if this parser can handle the given file.

        Checks if the file has a PDF extension (case-insensitive).

        Args:
            file_path: Path to the file to be parsed

        Returns:
            True if file has .pdf extension (case-insensitive), False otherwise

        Example:
            >>> parser = PDFStatementParser(detector)
            >>> assert parser.can_parse(Path("statement.pdf")) is True
            >>> assert parser.can_parse(Path("statement.PDF")) is True
            >>> assert parser.can_parse(Path("statement.xls")) is False
        """
        return file_path.suffix.lower() == ".pdf"

    def parse(self, file_path: Path) -> Statement:
        """
        Parse the PDF file and return a Statement object.

        Extracts raw text from the PDF using pdfplumber and creates a
        Statement object with the detected payment method. This skeleton
        implementation returns a statement with zero transactions.

        Args:
            file_path: Path to the PDF file to parse

        Returns:
            Statement object with detected payment method and empty transactions

        Raises:
            FileNotFoundError: If the input file does not exist
            ValueError: If the file format is invalid or cannot be parsed
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during file processing

        Example:
            >>> parser = PDFStatementParser(detector)
            >>> statement = parser.parse(Path("statement.pdf"))
            >>> assert isinstance(statement, Statement)
            >>> assert len(statement.transactions) == 0  # Skeleton implementation
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            # Extract raw text from PDF (skeleton: not used yet)
            # raw_text = self._extract_text(file_path)

            # Detect payment method from content/filename
            # For skeleton implementation, default to BBVA_VISA
            # In full implementation, this would use the detector
            payment_method = PaymentMethod.BBVA_VISA

            # Create and return Statement with zero transactions (skeleton)
            statement = Statement(payment_method=payment_method)
            return statement

        except PermissionError as e:
            raise PermissionError(
                f"Permission denied reading PDF file: {file_path}"
            ) from e
        except Exception as e:
            raise OSError(f"Error processing PDF file {file_path}: {str(e)}") from e

    def get_supported_extensions(self) -> set[str]:
        """
        Return the set of file extensions supported by this parser.

        Returns:
            Set containing '.pdf' extension

        Example:
            >>> parser = PDFStatementParser(detector)
            >>> extensions = parser.get_supported_extensions()
            >>> assert extensions == {'.pdf'}
        """
        return {".pdf"}

    def _extract_text(self, file_path: Path) -> str:
        """
        Helper method to extract raw text from PDF using pdfplumber.

        This method handles the low-level PDF text extraction using pdfplumber,
        which is proven to work well with Argentine bank statement formats.

        Args:
            file_path: Path to the PDF file

        Returns:
            Raw text content extracted from the PDF

        Raises:
            ValueError: If PDF cannot be opened or read
            OSError: If there's an I/O error during extraction

        Example:
            >>> parser = PDFStatementParser(detector)
            >>> text = parser._extract_text(Path("statement.pdf"))
            >>> assert isinstance(text, str)
            >>> assert len(text) > 0
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                text_content = []

                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)

                if not text_content:
                    raise ValueError(f"No text content found in PDF: {file_path}")

                return "\n".join(text_content)

        except Exception as e:
            raise ValueError(
                f"Failed to extract text from PDF {file_path}: {str(e)}"
            ) from e
