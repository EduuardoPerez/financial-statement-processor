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

_DATE_PATTERN = r"(\d{2}\.\d{2}\.\d{2})\s+"
_DATE_PATTERN_MMM = r"(\d{2}-\w{3}-\d{2})\s+"
_TAX_KEYWORDS = (
    "IMPUESTO DE SELLOS",
    "DB.IMPUESTO PAIS",
    "IIBB PERCEP",
    "IVA RG",
    "DB.RG",
)
_SKIP_KEYWORDS = ("SALDO ANTERIOR", "Total Consumos")
_BBVA_MC_SKIP_KEYWORDS = ("SALDO ACTUAL", "VENCIMIENTO", "PAGO MÍNIMO")


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
        statement, _ = self.parse_with_content(file_path)
        return statement

    def parse_with_content(self, file_path: Path) -> tuple[Statement, str]:
        """
        Parse the PDF file and return Statement with raw content.

        This method extracts raw text from the PDF and returns both the
        parsed Statement object and the raw text content for enhanced
        validation with balance extraction.

        Args:
            file_path: Path to the PDF file to parse

        Returns:
            Tuple of (Statement object, raw text content)

        Raises:
            FileNotFoundError: If the input file does not exist
            ValueError: If the file format is invalid or cannot be parsed
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during file processing

        Example:
            >>> parser = PDFStatementParser(detector, transaction_builder)
            >>> statement, content = parser.parse_with_content(Path("stmt.pdf"))
            >>> assert isinstance(statement, Statement)
            >>> assert len(content) > 0
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

            return statement, raw_text

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
        """Parse transaction lines from PDF text into Transaction objects."""
        transactions: list[Transaction] = []

        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line:
                continue

            match = re.match(_DATE_PATTERN, line)
            match_mmm = re.match(_DATE_PATTERN_MMM, line)

            if match:
                date_str = match.group(1)
                remaining_line = line[match.end() :].strip()
                is_mmm_date = False
            elif match_mmm:
                date_str = match_mmm.group(1)
                remaining_line = line[match_mmm.end() :].strip()
                is_mmm_date = True
            else:
                continue

            if any(kw in remaining_line for kw in _SKIP_KEYWORDS):
                continue

            if payment_method == PaymentMethod.BBVA_MASTERCARD and is_mmm_date:
                txn = self._try_parse_bbva_mastercard_line(
                    date_str, remaining_line, payment_method
                )
                if txn is not None:
                    transactions.append(txn)
                continue

            txn = (
                self._try_parse_tax(date_str, remaining_line, payment_method)
                or self._try_parse_fixed_keyword(
                    date_str,
                    remaining_line,
                    payment_method,
                    trigger="SU PAGO EN PESOS",
                    description="SU PAGO EN PESOS",
                    currency=Currency.ARS,
                )
                or self._try_parse_fixed_keyword(
                    date_str,
                    remaining_line,
                    payment_method,
                    trigger="SU PAGO EN USD",
                    description="SU PAGO EN USD",
                    currency=Currency.USD,
                )
                or self._try_parse_fixed_keyword(
                    date_str,
                    remaining_line,
                    payment_method,
                    trigger="AJUSTE",
                    description="AJUSTE P/DESCNTO. EN COMERCIO",
                    currency=Currency.ARS,
                    amount_pattern=r"([\d,.]+)-?\s*$",
                )
                or self._try_parse_keyword_with_desc(
                    date_str,
                    remaining_line,
                    payment_method,
                    trigger="BONIF.",
                )
                or self._try_parse_promo(date_str, remaining_line, payment_method)
                or self._try_parse_referenced(date_str, remaining_line, payment_method)
            )
            if txn is not None:
                transactions.append(txn)

        return transactions

    def _build(
        self,
        date_str: str,
        description: str,
        amount_str: str,
        currency: Currency,
        payment_method: PaymentMethod,
    ) -> Transaction | None:
        """Thin wrapper around TransactionBuilder that swallows ValueError."""
        try:
            return self._transaction_builder.build_from_pdf_line(
                date_str=date_str,
                description=description,
                amount_str=amount_str,
                currency=currency,
                payment_method=payment_method,
            )
        except ValueError:
            return None

    def _try_parse_tax(
        self, date_str: str, remaining_line: str, payment_method: PaymentMethod
    ) -> Transaction | None:
        if not any(tax in remaining_line for tax in _TAX_KEYWORDS):
            return None
        amount_match = re.search(r"([\d.,]+)(-?)\s*_?$", remaining_line)
        if not amount_match:
            return None
        amount_str = amount_match.group(1)
        sign = "-" if amount_match.group(2) else ""
        description = remaining_line.rsplit(amount_match.group(0), 1)[0].strip()
        return self._build(
            date_str, description, f"{sign}{amount_str}", Currency.ARS, payment_method
        )

    def _try_parse_fixed_keyword(
        self,
        date_str: str,
        remaining_line: str,
        payment_method: PaymentMethod,
        *,
        trigger: str,
        description: str,
        currency: Currency,
        amount_pattern: str = r"([\d,.]+)-?\s*_?$",
    ) -> Transaction | None:
        if trigger not in remaining_line:
            return None
        amount_match = re.search(amount_pattern, remaining_line)
        if not amount_match:
            return None
        amount_str = amount_match.group(1)
        return self._build(
            date_str, description, f"-{amount_str}", currency, payment_method
        )

    def _try_parse_keyword_with_desc(
        self,
        date_str: str,
        remaining_line: str,
        payment_method: PaymentMethod,
        *,
        trigger: str,
    ) -> Transaction | None:
        if trigger not in remaining_line:
            return None
        amount_match = re.search(r"([\d,.]+)-?\s*_?$", remaining_line)
        if not amount_match:
            return None
        amount_str = amount_match.group(1)
        description = remaining_line.rsplit(amount_match.group(0), 1)[0].strip()
        return self._build(
            date_str, description, f"-{amount_str}", Currency.ARS, payment_method
        )

    def _try_parse_promo(
        self, date_str: str, remaining_line: str, payment_method: PaymentMethod
    ) -> Transaction | None:
        if "OFF " not in remaining_line and "Promo" not in remaining_line:
            return None
        amount_match = re.search(r"([\d,.]+)-?\s*_?$", remaining_line)
        if not amount_match:
            return None
        amount_str = amount_match.group(1)
        description = remaining_line.rsplit(amount_match.group(0), 1)[0].strip()
        return self._build(
            date_str, description, f"-{amount_str}", Currency.ARS, payment_method
        )

    def _try_parse_bbva_mastercard_line(
        self, date_str: str, remaining_line: str, payment_method: PaymentMethod
    ) -> Transaction | None:
        if (
            len(remaining_line.split()) < 2
            or any(kw in remaining_line for kw in _BBVA_MC_SKIP_KEYWORDS)
            or remaining_line.count("-") > 2
            or re.match(
                r"\d{2}-\w{3}-\d{2}\s+[\d,.]+\s+[\d,.]+\s+[\d,.]+", remaining_line
            )
        ):
            return None

        if "SU PAGO EN PESOS" in remaining_line:
            amount_match = re.search(r"(-?[\d,.]+)$", remaining_line)
            if not amount_match:
                return None
            amount_str = amount_match.group(1).lstrip("-")
            return self._build(
                date_str,
                "SU PAGO EN PESOS",
                f"-{amount_str}",
                Currency.ARS,
                payment_method,
            )

        usd_match = re.search(r"USD\s+([\d,.-]+)", remaining_line)
        if usd_match:
            amount_str = usd_match.group(1).replace(",", ".")
            desc_before_usd = remaining_line.split("USD")[0].strip()
            full_description = f"{desc_before_usd} USD {usd_match.group(1)}".strip()
            return self._build(
                date_str, full_description, amount_str, Currency.USD, payment_method
            )

        amount_match = re.search(r"([\d,.]+)$", remaining_line)
        if not amount_match:
            return None
        amount_str = amount_match.group(1)
        description = remaining_line.rsplit(amount_str, 1)[0].strip()
        if len(description.split()) < 2:
            return None
        return self._build(
            date_str, description, amount_str, Currency.ARS, payment_method
        )

    def _try_parse_referenced(
        self, date_str: str, remaining_line: str, payment_method: PaymentMethod
    ) -> Transaction | None:
        ref_match = re.match(r"([A-Z0-9*]+[*KQVF]?)\s+", remaining_line)
        if not ref_match:
            return None
        after_ref = remaining_line[ref_match.end() :].strip()

        usd_match = re.search(r"USD\s+([\d,.-]+)", after_ref)
        if usd_match:
            amount_str = usd_match.group(1).replace(",", ".")
            desc_before_usd = after_ref.split("USD")[0].strip()
            full_description = f"{desc_before_usd} USD {usd_match.group(1)}".strip()
            return self._build(
                date_str, full_description, amount_str, Currency.USD, payment_method
            )

        for pattern in (
            r"(\d{1,3}(?:\.\d{3})*,\d{2})(-?)\s*$",
            r"(\d+,\d{2})(-?)\s*$",
            r"(\d+\.\d{2})(-?)\s*$",
            r"(\d+)(-?)\s*$",
        ):
            amount_match = re.search(pattern, after_ref)
            if not amount_match:
                continue
            amount_str = amount_match.group(1)
            sign = "-" if amount_match.group(2) else ""
            description = after_ref.rsplit(amount_match.group(0), 1)[0].strip()
            txn = self._build(
                date_str,
                description,
                f"{sign}{amount_str}",
                Currency.ARS,
                payment_method,
            )
            if txn is not None:
                return txn

        # Fallback: European amount anywhere in the line. A trailing "-" right
        # after the amount marks a refund, so propagate it as a negative sign.
        fallback_matches = list(
            re.finditer(r"(\d{1,3}(?:\.\d{3})*,\d{2})(-?)", after_ref)
        )
        if fallback_matches:
            last = fallback_matches[-1]
            amount_str = last.group(1)
            sign = "-" if last.group(2) else ""
            description = (after_ref[: last.start()] + after_ref[last.end() :]).strip()
            txn = self._build(
                date_str,
                description,
                f"{sign}{amount_str}",
                Currency.ARS,
                payment_method,
            )
            if txn is not None:
                return txn

        # Last resort: any comma-decimal-looking number
        for num in reversed(re.findall(r"[\d,.-]+", after_ref)):
            if "," not in num or len(num.split(",")[-1]) != 2:
                continue
            try:
                if self._amount_parser.parse_european_format(num) <= 0:
                    continue
            except ValueError:
                continue
            description = after_ref.replace(num, "").strip()
            txn = self._build(date_str, description, num, Currency.ARS, payment_method)
            if txn is not None:
                return txn

        return None
