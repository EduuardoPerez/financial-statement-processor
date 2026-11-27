"""
PDF statement parser implementation for the Financial Statement Processor.

This module provides a concrete implementation of the StatementParser interface
for processing PDF financial statements using pdfplumber for text extraction.

Classes:
    PDFStatementParser: PDF statement parser using pdfplumber for text extraction
"""

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pdfplumber

from domain.builders import TransactionBuilder
from domain.models import Currency, PaymentMethod, Statement, Transaction
from domain.services import StatementParser
from domain.utils import AmountParser, DateConverter

from ._shared import extraction_for_file, retain_transaction, verify_file_unchanged

_DATE_PATTERN = r"(\d{2}\.\d{2}\.\d{2})\s+"
_DATE_PATTERN_MMM = r"(\d{2}-\w{3}-\d{2})\s+"
_TAX_KEYWORDS = (
    "IMPUESTO DE SELLOS",
    "DB.IMPUESTO PAIS",
    "IIBB PERCEP",
    "IVA RG",
    "DB.RG",
    "CR.RG",
)
_COMMISSION_KEYWORDS = ("COMISIÓN", "COMISION")
_SKIP_KEYWORDS = ("SALDO ANTERIOR", "Total Consumos")
_BBVA_MC_SKIP_KEYWORDS = ("SALDO ACTUAL", "VENCIMIENTO", "PAGO MÍNIMO")
_MC_DATE = r"\d{2}-[A-Za-z]{3}-\d{2}"
_MC_CURRENT_ROW = re.compile(
    rf"^({_MC_DATE})\s+{_MC_DATE}\s+[\d.,]+\s+[\d.,]+\s+[\d.,]+$"
)
_MC_PREVIOUS_ROW = re.compile(rf"^({_MC_DATE})(?:\s+{_MC_DATE}){{3}}$")


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
            report = extraction_for_file(file_path)
            # Extract raw text from PDF
            raw_text = self._extract_text(file_path)

            # Detect payment method from content
            payment_method = self._detector.detect_from_content(raw_text)

            # Create statement
            statement = Statement(payment_method=payment_method)
            statement.extraction = report

            # Parse transactions from text
            transactions = self._parse_transactions(raw_text, payment_method, report)

            # Add transactions to statement
            for transaction in transactions:
                statement.add_transaction(transaction)

            verify_file_unchanged(file_path, report)
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
        self, text: str, payment_method: PaymentMethod, report=None
    ) -> list[Transaction]:
        """Parse transaction lines from PDF text into Transaction objects."""
        transactions: list[Transaction] = []
        lines = text.split("\n")

        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue
            preceding = " ".join(
                lines[max(0, line_number - 3) : line_number - 1]
            ).upper()
            if payment_method == PaymentMethod.BBVA_MASTERCARD and (
                (_MC_CURRENT_ROW.fullmatch(line) and "CIERRE ACTUAL" in preceding)
                or (_MC_PREVIOUS_ROW.fullmatch(line) and "CIERRE ANTERIOR" in preceding)
            ):
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
            if payment_method == PaymentMethod.BBVA_MASTERCARD and any(
                kw in remaining_line for kw in _BBVA_MC_SKIP_KEYWORDS
            ):
                continue

            locator = f"line:{line_number}"

            def record(transaction: Transaction | None) -> None:
                if transaction is None:
                    if report is not None:
                        report.discard(
                            locator, "Unrecognized or invalid transaction line"
                        )
                    return
                source_amount = (
                    re.search(r"USD\s+([\d,.-]+)", remaining_line)
                    if transaction.currency == Currency.USD
                    else None
                )
                if source_amount:
                    raw_amount = source_amount.group(1)
                else:
                    trailing_amount = re.search(
                        r"([+-]?[\d.,]+-?)\s*_?$", remaining_line
                    )
                    raw_amount = trailing_amount.group(1) if trailing_amount else ""
                if not raw_amount:
                    for candidate in reversed(re.findall(r"[\d.,]+-?", remaining_line)):
                        try:
                            if abs(
                                self._amount_parser.parse_european_format(candidate)
                            ) == abs(transaction.amount):
                                raw_amount = candidate
                                break
                        except ValueError:
                            continue
                source_reference = re.match(
                    r"((?=[A-Z0-9*]*\d)[A-Z0-9*]+)\s+", remaining_line
                )
                installment = re.search(r"\bCuota\s+(\d+/\d+)\b", remaining_line)
                references = {}
                if source_reference:
                    references["source_reference"] = source_reference.group(1)
                if installment:
                    references["Cuota"] = installment.group(1)
                transactions.append(
                    retain_transaction(
                        transaction,
                        report,
                        locator,
                        date_str,
                        raw_amount,
                        remaining_line,
                        raw_currency="USD" if "USD " in remaining_line else None,
                        references=references,
                    )
                )

            if payment_method == PaymentMethod.BBVA_MASTERCARD and is_mmm_date:
                txn = self._try_parse_bbva_mastercard_line(
                    date_str, remaining_line, payment_method
                )
                record(txn)
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
                or self._try_parse_commission(date_str, remaining_line, payment_method)
                or self._try_parse_referenced(date_str, remaining_line, payment_method)
            )
            record(txn)

        return transactions

    @staticmethod
    def statement_cycle(content: str) -> tuple[date, date] | None:
        """Return the verified previous-to-current Mastercard close interval."""
        current: date | None = None
        previous: date | None = None
        converter = DateConverter()
        lines = content.splitlines()
        for index, line in enumerate(lines):
            stripped = line.strip()
            current_match = _MC_CURRENT_ROW.fullmatch(stripped)
            previous_match = _MC_PREVIOUS_ROW.fullmatch(stripped)
            preceding = " ".join(lines[max(0, index - 2) : index]).upper()
            try:
                if current_match and "CIERRE ACTUAL" in preceding:
                    current = converter.convert_dd_mmm_yy(
                        current_match.group(1).title()
                    )
                if previous_match and "CIERRE ANTERIOR" in preceding:
                    previous = converter.convert_dd_mmm_yy(
                        previous_match.group(1).title()
                    )
            except ValueError:
                return None
        if current is None or previous is None or previous >= current:
            return None
        return previous + timedelta(days=1), current

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
        return self._build_from_trailing_signed_amount(
            date_str, remaining_line, payment_method
        )

    def _build_from_trailing_signed_amount(
        self, date_str: str, remaining_line: str, payment_method: PaymentMethod
    ) -> Transaction | None:
        """Build an ARS transaction from a line ending in an amount with an
        optional '-' sign (and tolerating a stray trailing '_'); the rest of
        the line becomes the description."""
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

    def _try_parse_commission(
        self, date_str: str, remaining_line: str, payment_method: PaymentMethod
    ) -> Transaction | None:
        # Card-fee lines carry no reference code, and the accented "Ó" in
        # "COMISIÓN" falls outside the ASCII-only reference regex, so they
        # need their own handler. Only lines starting with the keyword are
        # fees; refunds ("DEV COMISIÓN ...") keep going through the
        # referenced handler.
        if not remaining_line.startswith(_COMMISSION_KEYWORDS):
            return None
        return self._build_from_trailing_signed_amount(
            date_str, remaining_line, payment_method
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
