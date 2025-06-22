r"""
Domain service for generating standardized output filenames.

This module provides the FilenameGenerator class that creates filenames
from statement payment methods and first transaction dates, following
the pattern ^[A-Z_]+_\d{8}\.xlsx$.
"""

from .models import PaymentMethod, Statement


class FilenameGenerator:
    """Domain service for generating standardized output filenames."""

    def generate(self, statement: Statement) -> str:
        r"""
        Generate filename from statement payment method and first transaction.

        Args:
            statement: Statement object containing transactions

        Returns:
            Filename matching pattern ^[A-Z_]+_\d{8}\.xlsx$

        Raises:
            ValueError: If statement has no transactions

        Example:
            >>> generator = FilenameGenerator()
            >>> statement = Statement(
            ...     PaymentMethod.BBVA_VISA, transactions=[...]
            ... )
            >>> filename = generator.generate(statement)
            >>> print(filename)  # "BBVA_VISA_20250328.xlsx"
        """
        if not statement.transactions:
            raise ValueError(
                "Cannot generate filename for statement with no transactions"
            )

        # Get payment method prefix
        method_prefix = self._get_method_prefix(statement.payment_method)

        # Get first transaction date (earliest date)
        first_date = min(t.date for t in statement.transactions)
        date_suffix = first_date.strftime("%Y%m%d")

        return f"{method_prefix}_{date_suffix}.xlsx"

    def _get_method_prefix(self, payment_method: PaymentMethod) -> str:
        """
        Map payment method to filename prefix.

        Args:
            payment_method: PaymentMethod enum value

        Returns:
            Uppercase prefix with underscores for filename

        Example:
            >>> generator = FilenameGenerator()
            >>> prefix = generator._get_method_prefix(PaymentMethod.BBVA_VISA)
            >>> print(prefix)  # "BBVA_VISA"
        """
        mapping = {
            PaymentMethod.BBVA_VISA: "BBVA_VISA",
            PaymentMethod.BBVA_MASTERCARD: "BBVA_MASTERCARD",
            PaymentMethod.BBVA_ACCOUNT: "BBVA_ACCOUNT",
            PaymentMethod.MACRO_VISA: "MACRO_VISA",
            PaymentMethod.MACRO_ACCOUNT: "MACRO_ACCOUNT",
            PaymentMethod.MERCADOPAGO: "MERCADOPAGO",
        }

        # Use mapping if available, otherwise convert enum value to uppercase
        # with underscores
        return mapping.get(
            payment_method, payment_method.value.upper().replace(" ", "_")
        )
