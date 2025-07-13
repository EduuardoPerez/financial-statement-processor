"""
Balance extraction implementations for the Financial Statement Processor.

This module provides concrete implementations of the BalanceExtractor interface
for extracting reported balances from different statement formats.

Classes:
    PDFBalanceExtractor: Extracts balances from PDF content using regex
    BalanceExtractionService: Registry-based service for managing extractors
"""

import re
from decimal import Decimal
from pathlib import Path

from domain.models import PaymentMethod
from domain.services import BalanceExtractor


class PDFBalanceExtractor(BalanceExtractor):
    """Concrete extractor for PDF balance extraction using regex patterns."""

    def extract_balance(
        self, content: str, payment_method: PaymentMethod
    ) -> dict[str, Decimal]:
        """Extract reported balance from PDF text using payment patterns."""
        balance = {"ars": Decimal("0.0"), "usd": Decimal("0.0")}

        if payment_method == PaymentMethod.BBVA_MASTERCARD:
            # BBVA Mastercard format ARS and USD
            pattern1 = r"SALDO ACTUAL \$ ([\d,.]+).*?" r"SALDO ACTUAL U\$S ([\d,.]+)"
            match1 = re.search(pattern1, content)
            if match1:
                ars_str = match1.group(1)
                usd_str = match1.group(2)
            else:
                # Alternative pattern for BBVA Mastercard
                pattern2 = (
                    r"\d{2}-\w{3}-\d{2}\s+\d{2}-\w{3}-\d{2}\s+([\d,.]+)\s+"
                    r"([\d,.]+)\s+[\d,.]+"
                )
                match2 = re.search(pattern2, content)
                if match2:
                    ars_str = match2.group(1)
                    usd_str = match2.group(2)
                else:
                    ars_str = "0"
                    usd_str = "0"
        else:
            # Standard format for MACRO VISA and BBVA VISA
            # Flexible spacing and optional USD
            # Pattern 1: Both ARS and USD amounts present
            pattern1 = r"SALDO ACTUAL\s+\$\s+([\d,.]+)\s+U\$S\s+([\d,.]+)"
            match1 = re.search(pattern1, content)
            if match1:
                ars_str = match1.group(1)
                usd_str = match1.group(2)
            else:
                # Pattern 2: Only ARS amount present (more flexible)
                pattern2 = r"SALDO ACTUAL\s+\$\s+([\d,.]+)"
                match2 = re.search(pattern2, content)
                if match2:
                    ars_str = match2.group(1)
                    usd_str = "0"
                else:
                    ars_str = "0"
                    usd_str = "0"

        # Convert European format to decimal
        balance["ars"] = self._parse_european_amount(ars_str)
        balance["usd"] = self._parse_european_amount(usd_str)

        return balance

    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """Check if extractor supports PDF-based payment methods."""
        pdf_methods = {
            PaymentMethod.BBVA_VISA,
            PaymentMethod.BBVA_MASTERCARD,
            PaymentMethod.MACRO_VISA,
        }
        return payment_method in pdf_methods

    def _parse_european_amount(self, amount_str: str) -> Decimal:
        """Convert European format (1.234,56) to Decimal."""
        try:
            # Handle European format for amounts
            if "." in amount_str and "," in amount_str:
                amount_str = amount_str.replace(".", "").replace(",", ".")
            elif "," in amount_str:
                amount_str = amount_str.replace(",", ".")
            return Decimal(amount_str)
        except (ValueError, TypeError, Exception):
            return Decimal("0.0")


class CSVBalanceExtractor(BalanceExtractor):
    """Extractor for CSV file balance validation."""

    def extract_balance(
        self, content: str, payment_method: PaymentMethod
    ) -> dict[str, Decimal]:
        """Extract total from CSV file for validation."""
        import pandas as pd

        try:
            # Treat content as file path for CSV
            file_path = Path(content)
            df = pd.read_csv(file_path, sep=";")
            total = Decimal("0.0")

            for _, row in df.iterrows():
                importe_str = str(row["Importe"]).strip()
                if importe_str and importe_str != "nan":
                    try:
                        # Handle European format
                        amount_str = importe_str.replace(",", "")
                        amount = Decimal(amount_str)
                        total += amount
                    except (ValueError, TypeError, Exception):
                        continue

            # CSV files are typically ARS only
            return {"ars": total, "usd": Decimal("0.0")}

        except Exception:
            return {"ars": Decimal("0.0"), "usd": Decimal("0.0")}

    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """Check if extractor supports CSV-based payment methods."""
        csv_methods = {PaymentMethod.BBVA_VISA, PaymentMethod.MACRO_VISA}
        return payment_method in csv_methods


class XLSXBalanceExtractor(BalanceExtractor):
    """Extractor for XLSX file balance validation."""

    def extract_balance(
        self, content: str, payment_method: PaymentMethod
    ) -> dict[str, Decimal]:
        """Extract total from XLSX file for validation."""
        import pandas as pd

        try:
            # Treat content as file path for XLSX
            file_path = Path(content)
            df = pd.read_excel(file_path)
            total = Decimal("0.0")

            for _, row in df.iterrows():
                importe = row["Importe"] if pd.notna(row["Importe"]) else 0
                try:
                    amount = Decimal(str(importe))
                    total += amount
                except (ValueError, TypeError, Exception):
                    continue

            # XLSX files (Mercadopago) are typically ARS only
            return {"ars": total, "usd": Decimal("0.0")}

        except Exception:
            return {"ars": Decimal("0.0"), "usd": Decimal("0.0")}

    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """Check if extractor supports XLSX-based payment methods."""
        return payment_method == PaymentMethod.MERCADOPAGO


class BalanceExtractionService:
    """Service managing multiple balance extractors using registry pattern."""

    def __init__(self):
        self._extractors: list[BalanceExtractor] = []

    def register_extractor(self, extractor: BalanceExtractor) -> None:
        """Register a balance extractor."""
        self._extractors.append(extractor)

    def extract_balance(
        self, content: str, payment_method: PaymentMethod
    ) -> dict[str, Decimal] | None:
        """Extract balance using appropriate extractor."""
        for extractor in self._extractors:
            if extractor.can_extract(payment_method):
                return extractor.extract_balance(content, payment_method)
        return None


def build_default_balance_service() -> BalanceExtractionService:
    """Build balance service with all standard extractors."""
    service = BalanceExtractionService()
    service.register_extractor(PDFBalanceExtractor())
    service.register_extractor(CSVBalanceExtractor())
    service.register_extractor(XLSXBalanceExtractor())
    return service
