"""
PDF statement parser implementation for the Financial Statement Processor.

This module provides a concrete implementation of the StatementParser interface
for processing PDF financial statements using pdfplumber for text extraction.

Classes:
    PDFStatementParser: PDF statement parser using pdfplumber for text extraction
"""

import re
from pathlib import Path
from typing import Any

import pdfplumber

from domain.builders import TransactionBuilder
from domain.models import Currency, PaymentMethod, Statement, Transaction
from domain.services import StatementParser
from domain.utils import AmountParser

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

    def __init__(self, detector: Any, transaction_builder: TransactionBuilder) -> None:
        """
        Initialize PDF parser with payment method detector and transaction builder.

        Args:
            detector: Payment method detector for identifying bank/card type
                     from PDF content or filename
            transaction_builder: TransactionBuilder for constructing Transaction
                                objects from parsed PDF line components
        """
        self._detector = detector
        self._transaction_builder = transaction_builder
        # Extract amount parser from transaction builder for direct use
        self._amount_parser: AmountParser = transaction_builder._amount_parser

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
        Parse the PDF file and return a Statement object with transactions.

        Extracts raw text from the PDF using pdfplumber, detects the payment
        method, parses transaction lines, and creates a Statement object
        populated with Transaction objects built using the TransactionBuilder.

        Args:
            file_path: Path to the PDF file to parse

        Returns:
            Statement object with detected payment method and parsed transactions

        Raises:
            FileNotFoundError: If the input file does not exist
            ValueError: If the file format is invalid or cannot be parsed
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during file processing

        Example:
            >>> parser = PDFStatementParser(detector, transaction_builder)
            >>> statement = parser.parse(Path("statement.pdf"))
            >>> assert isinstance(statement, Statement)
            >>> assert len(statement.transactions) > 0
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            # Extract raw text from PDF
            raw_text = self._extract_text(file_path)

            # Detect payment method from content
            payment_method = self._detector.detect_from_content(raw_text)

            # Create statement
            statement = Statement(payment_method=payment_method)

            # Parse transactions from text
            transactions = self._parse_transactions(raw_text, payment_method)

            # Add transactions to statement
            for transaction in transactions:
                statement.add_transaction(transaction)

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

    def _parse_transactions(
        self, text: str, payment_method: PaymentMethod
    ) -> list[Transaction]:
        """
        Parse transaction lines from PDF text using sophisticated logic from working parser.

        Implements the task requirements:
        1. Split lines on ≥ 2 spaces (when needed for parsing)
        2. Build Transactions (currency = ARS default, USD when detected)
        3. Append to Statement

        Args:
            text: Raw text extracted from PDF
            payment_method: Detected payment method for transactions

        Returns:
            List of parsed Transaction objects

        Example:
            >>> transactions = parser._parse_transactions(pdf_text, method)
            >>> assert len(transactions) > 0
        """
        transactions = []
        lines = text.split("\n")

        # Pattern for transaction lines with date
        date_pattern = r"(\d{2}\.\d{2}\.\d{2})\s+"
        date_pattern_mmm = r"(\d{2}-\w{3}-\d{2})\s+"  # BBVA Mastercard format

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            match = re.match(date_pattern, line)
            match_mmm = re.match(date_pattern_mmm, line)

            if match:
                date_str = match.group(1)
                remaining_line = line[match.end() :].strip()
            elif match_mmm:
                date_str = match_mmm.group(1)
                remaining_line = line[match_mmm.end() :].strip()
            else:
                continue

            # Skip certain lines
            if "SALDO ANTERIOR" in remaining_line or "Total Consumos" in remaining_line:
                continue

            # Handle BBVA Mastercard single-line format
            if payment_method.value == "BBVA Mastercard" and match_mmm:
                if (
                    len(remaining_line.split()) < 2
                    or "SALDO ACTUAL" in remaining_line
                    or "VENCIMIENTO" in remaining_line
                    or remaining_line.count("-") > 2
                    or "PAGO MÍNIMO" in remaining_line
                    or re.match(
                        r"\d{2}-\w{3}-\d{2}\s+[\d,.]+\s+[\d,.]+\s+[\d,.]+",
                        remaining_line,
                    )
                ):
                    continue

                if "SU PAGO EN PESOS" in remaining_line:
                    amount_match = re.search(r"(-?[\d,.]+)$", remaining_line)
                    if amount_match:
                        amount_str = amount_match.group(1)
                        is_negative = amount_str.startswith("-")
                        if is_negative:
                            amount_str = amount_str[1:]

                        try:
                            transaction = self._transaction_builder.build_from_pdf_line(
                                date_str=date_str,
                                description="SU PAGO EN PESOS",
                                amount_str=f"-{amount_str}",  # Always negative for payments
                                currency=Currency.ARS,
                                payment_method=payment_method,
                            )
                            transactions.append(transaction)
                        except ValueError:
                            pass
                else:
                    amount_match = re.search(r"([\d,.]+)$", remaining_line)
                    if amount_match:
                        amount_str = amount_match.group(1)
                        description = remaining_line.rsplit(amount_match.group(1), 1)[
                            0
                        ].strip()
                        if len(description.split()) >= 2:
                            try:
                                transaction = (
                                    self._transaction_builder.build_from_pdf_line(
                                        date_str=date_str,
                                        description=description,
                                        amount_str=amount_str,
                                        currency=Currency.ARS,
                                        payment_method=payment_method,
                                    )
                                )
                                transactions.append(transaction)
                            except ValueError:
                                pass
                continue

            # Handle tax entries
            if any(
                tax in remaining_line
                for tax in [
                    "IMPUESTO DE SELLOS",
                    "DB.IMPUESTO PAIS",
                    "IIBB PERCEP",
                    "IVA RG",
                    "DB.RG",
                ]
            ):
                amount_match = re.search(r"([\d.,]+)$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    description = remaining_line.rsplit(amount_match.group(1), 1)[
                        0
                    ].strip()
                    try:
                        transaction = self._transaction_builder.build_from_pdf_line(
                            date_str=date_str,
                            description=description,
                            amount_str=amount_str,
                            currency=Currency.ARS,
                            payment_method=payment_method,
                        )
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle payment lines (SU PAGO EN PESOS)
            if "SU PAGO EN PESOS" in remaining_line:
                amount_match = re.search(r"([\d,.]+)-?\s*_?$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    try:
                        transaction = self._transaction_builder.build_from_pdf_line(
                            date_str=date_str,
                            description="SU PAGO EN PESOS",
                            amount_str=f"-{amount_str}",  # Always negative for payments
                            currency=Currency.ARS,
                            payment_method=payment_method,
                        )
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle USD payment lines (SU PAGO EN USD)
            if "SU PAGO EN USD" in remaining_line:
                amount_match = re.search(r"([\d,.]+)-?\s*_?$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    try:
                        transaction = self._transaction_builder.build_from_pdf_line(
                            date_str=date_str,
                            description="SU PAGO EN USD",
                            amount_str=f"-{amount_str}",  # Always negative for payments
                            currency=Currency.USD,
                            payment_method=payment_method,
                        )
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle adjustment lines
            if "AJUSTE" in remaining_line:
                amount_match = re.search(r"([\d,.]+)-?\s*$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    try:
                        transaction = self._transaction_builder.build_from_pdf_line(
                            date_str=date_str,
                            description="AJUSTE P/DESCNTO. EN COMERCIO",
                            amount_str=f"-{amount_str}",  # Always negative for adjustments
                            currency=Currency.ARS,
                            payment_method=payment_method,
                        )
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle BBVA bonification lines (BONIF.)
            if "BONIF." in remaining_line:
                amount_match = re.search(r"([\d,.]+)-?\s*$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    description = remaining_line.rsplit(amount_match.group(0), 1)[
                        0
                    ].strip()
                    try:
                        transaction = self._transaction_builder.build_from_pdf_line(
                            date_str=date_str,
                            description=description,
                            amount_str=f"-{amount_str}",  # Always negative for bonifications
                            currency=Currency.ARS,
                            payment_method=payment_method,
                        )
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle OFF/promo lines
            if "OFF " in remaining_line or "Promo" in remaining_line:
                amount_match = re.search(r"([\d,.]+)-?\s*$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    description = remaining_line.rsplit(amount_match.group(0), 1)[
                        0
                    ].strip()
                    try:
                        transaction = self._transaction_builder.build_from_pdf_line(
                            date_str=date_str,
                            description=description,
                            amount_str=f"-{amount_str}",  # Always negative for promos
                            currency=Currency.ARS,
                            payment_method=payment_method,
                        )
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Parse regular transactions - look for reference number pattern at start
            ref_match = re.match(r"([A-Z0-9*]+[*KQV]?)\s+", remaining_line)

            if ref_match:
                ref_number = ref_match.group(1)
                after_ref = remaining_line[ref_match.end() :].strip()

                # Check for USD transactions
                usd_match = re.search(r"USD\s+([\d,.-]+)", after_ref)
                if usd_match:
                    amount_str = usd_match.group(1).replace(",", ".")
                    desc_before_usd = after_ref.split("USD")[0].strip()
                    usd_amount_str = usd_match.group(1)
                    full_description = (
                        f"{ref_number} {desc_before_usd} USD {usd_amount_str}".strip()
                    )

                    try:
                        transaction = self._transaction_builder.build_from_pdf_line(
                            date_str=date_str,
                            description=full_description,
                            amount_str=amount_str,
                            currency=Currency.USD,
                            payment_method=payment_method,
                        )
                        transactions.append(transaction)
                    except ValueError:
                        pass
                    continue

                # For ARS transactions, find amount at the end
                amount_patterns = [
                    r"(\d{1,3}(?:\.\d{3})*,\d{2})$",  # 1.234,56 format
                    r"(\d+,\d{2})$",  # 123,45 format
                    r"(\d+\.\d{2})$",  # 123.45 format (US style)
                    r"(\d+)$",  # Integer amounts
                ]

                amount_found = False
                for pattern in amount_patterns:
                    amount_match = re.search(pattern, after_ref)
                    if amount_match:
                        amount_str = amount_match.group(1)
                        description = after_ref.rsplit(amount_match.group(1), 1)[
                            0
                        ].strip()
                        full_description = f"{ref_number} {description}".strip()

                        try:
                            transaction = self._transaction_builder.build_from_pdf_line(
                                date_str=date_str,
                                description=full_description,
                                amount_str=amount_str,
                                currency=Currency.ARS,
                                payment_method=payment_method,
                            )
                            transactions.append(transaction)
                            amount_found = True
                            break
                        except ValueError:
                            continue

                if not amount_found:
                    # Fallback: try to find European format amounts
                    european_amounts = re.findall(
                        r"\d{1,3}(?:\.\d{3})*,\d{2}", after_ref
                    )
                    if european_amounts:
                        amount_str = european_amounts[-1]
                        description = after_ref.replace(
                            european_amounts[-1], ""
                        ).strip()
                        full_description = f"{ref_number} {description}".strip()

                        try:
                            transaction = self._transaction_builder.build_from_pdf_line(
                                date_str=date_str,
                                description=full_description,
                                amount_str=amount_str,
                                currency=Currency.ARS,
                                payment_method=payment_method,
                            )
                            transactions.append(transaction)
                            continue
                        except ValueError:
                            pass

                    # Last resort: find any number-like pattern
                    numbers = re.findall(r"[\d,.-]+", after_ref)
                    if numbers:
                        for num in reversed(numbers):
                            try:
                                # Test if this looks like a valid amount
                                if "," in num and len(num.split(",")[-1]) == 2:
                                    test_amount = (
                                        self._amount_parser.parse_european_format(num)
                                    )
                                    if test_amount > 0:
                                        description = after_ref.replace(num, "").strip()
                                        full_description = (
                                            f"{ref_number} {description}".strip()
                                        )

                                        transaction = self._transaction_builder.build_from_pdf_line(
                                            date_str=date_str,
                                            description=full_description,
                                            amount_str=num,
                                            currency=Currency.ARS,
                                            payment_method=payment_method,
                                        )
                                        transactions.append(transaction)
                                        break
                            except ValueError:
                                continue

        return transactions
