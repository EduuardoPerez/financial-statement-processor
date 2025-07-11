"""
Utility classes for date conversion and amount parsing.

This module provides utility classes that follow the Single Responsibility
Principle, extracting date conversion and European number format parsing logic
into clean, focused utility classes for the clean architecture transformation.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal


class DateConverter:
    """
    Utility class for converting various date formats to standardized date
    objects.

    Handles multiple date formats commonly found in Argentine financial
    statements:
    - DD.MM.YY format (VISA statements)
    - DD-MMM-YY format (Mastercard statements)
    - Spanish month abbreviations
    """

    def __init__(self) -> None:
        """Initialize DateConverter with Spanish month mappings."""
        self._spanish_months = {
            "Jan": 1,
            "Ene": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "Abr": 4,  # Spanish April
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Ago": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
            "Dic": 12,
        }

    def convert_dd_mm_yy(self, date_str: str) -> date:
        """
        Convert DD.MM.YY format to date object.

        Args:
            date_str: Date string in DD.MM.YY format (e.g., "05.06.25")

        Returns:
            date: Parsed date object

        Raises:
            ValueError: If date string format is invalid

        Example:
            >>> converter = DateConverter()
            >>> converter.convert_dd_mm_yy("05.06.25")
            datetime.date(2025, 6, 5)
        """
        if not date_str or "." not in date_str:
            msg = f"Invalid date format: {date_str}. Expected DD.MM.YY"
            raise ValueError(msg)

        try:
            day_str, month_str, year_str = date_str.split(".")

            day = int(day_str)
            month = int(month_str)
            year_int = int(year_str)

            # Year logic: <50 = 2000s, >=50 = 1900s
            if year_int < 50:
                full_year = 2000 + year_int
            else:
                full_year = 1900 + year_int

            return date(full_year, month, day)

        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid date format: {date_str}. Expected DD.MM.YY"
            ) from e

    def convert_dd_mmm_yy(self, date_str: str) -> date:
        """
        Convert DD-MMM-YY format to date object.

        Supports both English and Spanish month abbreviations commonly found
        in BBVA Mastercard statements.

        Args:
            date_str: Date string in DD-MMM-YY format (e.g., "15-Mar-25",
                "04-Abr-25")

        Returns:
            date: Parsed date object

        Raises:
            ValueError: If date string format is invalid or month is
                unrecognized

        Example:
            >>> converter = DateConverter()
            >>> converter.convert_dd_mmm_yy("04-Abr-25")
            datetime.date(2025, 4, 4)
        """
        if not date_str or "-" not in date_str:
            msg = f"Invalid date format: {date_str}. Expected DD-MMM-YY"
            raise ValueError(msg)

        try:
            day_str, month_name, year_str = date_str.split("-")

            day = int(day_str)
            year_int = int(year_str)

            # Look up month number from Spanish/English abbreviations
            month = self._spanish_months.get(month_name)
            if month is None:
                msg = f"Unrecognized month abbreviation: {month_name}"
                raise ValueError(msg)

            # Year logic: <50 = 2000s, >=50 = 1900s
            if year_int < 50:
                full_year = 2000 + year_int
            else:
                full_year = 1900 + year_int

            return date(full_year, month, day)

        except (ValueError, TypeError) as e:
            if "Unrecognized month" in str(e):
                raise e
            raise ValueError(
                f"Invalid date format: {date_str}. Expected DD-MMM-YY"
            ) from e


class AmountParser:
    """
    Utility class for parsing European number format amounts to Decimal
    objects.

    Handles various European number formats commonly found in Argentine
    financial statements:
    - 1.234.567,89 (dots as thousands separators, comma as decimal)
    - 1234,56 (comma as decimal separator only)
    - 1500,75- (trailing dash for negative amounts)
    """

    def parse_european_format(self, amount_str: str) -> Decimal:
        """
        Parse European format number string to Decimal.

        Handles multiple European number formats with proper financial
        precision:
        - 1.234.567,89 -> 1234567.89
        - 1234,56 -> 1234.56
        - 1500,75- -> -1500.75

        Args:
            amount_str: Amount string in European format

        Returns:
            Decimal: Parsed amount with financial precision

        Raises:
            ValueError: If amount string cannot be parsed

        Example:
            >>> parser = AmountParser()
            >>> parser.parse_european_format("1.234,56")
            Decimal('1234.56')
        """
        if not amount_str or not amount_str.strip():
            raise ValueError("Amount string cannot be empty")

        # Clean the input string
        clean_str = amount_str.strip()

        # Handle negative amounts with trailing dash
        is_negative = clean_str.endswith("-")
        if is_negative:
            clean_str = clean_str[:-1].strip()

        # Handle negative amounts with leading dash
        if clean_str.startswith("-"):
            is_negative = True
            clean_str = clean_str[1:].strip()

        try:
            # Handle European format conversion
            if "." in clean_str and "," in clean_str:
                # Format: 1.234.567,89 -> remove dots (thousands), convert
                # comma to decimal
                clean_str = clean_str.replace(".", "").replace(",", ".")
            elif "," in clean_str:
                # Check if comma is decimal separator
                parts = clean_str.split(",")
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Format: 1234,56 -> convert comma to decimal point
                    clean_str = clean_str.replace(",", ".")
                else:
                    # Comma might be thousands separator, remove it
                    clean_str = clean_str.replace(",", "")

            # Parse to Decimal for financial precision
            amount = Decimal(clean_str)

            # Apply negative sign if needed
            if is_negative:
                amount = -amount

            return amount

        except (ValueError, TypeError, ArithmeticError) as e:
            raise ValueError(f"Cannot parse amount: {amount_str}") from e
