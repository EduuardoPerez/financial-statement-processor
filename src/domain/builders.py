"""
Builder classes for constructing domain objects.

This module provides builder classes that follow the Single Responsibility
Principle, focusing on the construction of complex domain objects with
proper validation and dependency injection for the clean architecture
transformation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Currency, PaymentMethod, Transaction
    from .utils import AmountParser, DateConverter

__all__ = ["TransactionBuilder"]


class TransactionBuilder:
    """
    Builder for constructing Transaction objects from parsed components.

    This class follows the Single Responsibility Principle by focusing solely
    on Transaction object construction. It uses injected DateConverter and
    AmountParser utilities to handle the parsing of date and amount components,
    then constructs properly validated Transaction objects.

    The builder is designed for use in PDF parsing workflows where transaction
    components are extracted from text lines and need to be converted into
    domain objects.
    """

    def __init__(
        self, date_converter: DateConverter, amount_parser: AmountParser
    ) -> None:
        """
        Initialize TransactionBuilder with injected dependencies.

        Args:
            date_converter: DateConverter instance for parsing date strings
            amount_parser: AmountParser instance for parsing European format
                amounts

        Example:
            >>> from domain.utils import DateConverter, AmountParser
            >>> builder = TransactionBuilder(
            ...     DateConverter(), AmountParser()
            ... )
        """
        self._date_converter = date_converter
        self._amount_parser = amount_parser

    def build_from_pdf_line(
        self,
        date_str: str,
        description: str,
        amount_str: str,
        currency: Currency,
        payment_method: PaymentMethod,
    ) -> Transaction:
        """
        Build Transaction object from PDF line components.

        Takes the individual components extracted from a PDF transaction line
        and constructs a properly validated Transaction domain object using
        the injected utility parsers.

        Args:
            date_str: Date string in DD.MM.YY format (e.g., "05.06.25")
            description: Transaction description text
            amount_str: Amount string in European format (e.g., "1.234,56")
            currency: Currency enum value (ARS or USD)
            payment_method: PaymentMethod enum value

        Returns:
            Transaction: Properly constructed and validated Transaction object

        Raises:
            ValueError: If any component cannot be parsed or validation fails

        Example:
            >>> from domain.models import Currency, PaymentMethod
            >>> transaction = builder.build_from_pdf_line(
            ...     date_str="05.06.25",
            ...     description="COMPRA EN COMERCIO",
            ...     amount_str="1.234,56",
            ...     currency=Currency.ARS,
            ...     payment_method=PaymentMethod.BBVA_VISA
            ... )
            >>> transaction.date.year
            2025
            >>> transaction.amount
            Decimal('1234.56')
        """
        # Import here to avoid circular imports
        from .models import Transaction

        if not date_str or not date_str.strip():
            raise ValueError("Date string cannot be empty")

        if not description or not description.strip():
            raise ValueError("Description cannot be empty")

        if not amount_str or not amount_str.strip():
            raise ValueError("Amount string cannot be empty")

        try:
            # Use injected DateConverter to parse date
            date_clean = date_str.strip()
            parsed_date = self._date_converter.convert_dd_mm_yy(date_clean)

            # Use injected AmountParser to parse amount
            parsed_amount = self._amount_parser.parse_european_format(
                amount_str.strip()
            )

            # Clean description
            clean_description = description.strip()

            # Construct Transaction using domain model
            transaction = Transaction(
                date=parsed_date,
                description=clean_description,
                amount=parsed_amount,
                currency=currency,
                payment_method=payment_method,
            )

            return transaction

        except ValueError as e:
            # Re-raise with context about which component failed
            msg = f"Failed to build transaction from PDF line components: {e}"
            raise ValueError(msg) from e
        except Exception as e:
            # Handle unexpected errors
            msg = f"Unexpected error building transaction: {str(e)}"
            raise ValueError(msg) from e
