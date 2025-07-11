"""
Concrete bank detector implementations for the Financial Statement Processor.

This module provides concrete implementations of the BankDetector abstract
base class, enabling specific bank identification logic for different
financial institutions. These detectors are used by the PaymentMethodDetector
to identify payment methods from statement content.

Classes:
    MacroDetector: Detector for Macro bank statements
    BBVADetector: Detector for BBVA bank statements

Functions:
    build_default_payment_detector: Factory function to create a detector
                                   with all standard bank detectors registered
"""

from domain.detectors import BankDetector, PaymentMethodDetector
from domain.models import PaymentMethod


class MacroDetector(BankDetector):
    """
    Concrete detector for Macro bank statements.

    This detector identifies Macro bank statements by looking for specific
    indicators in the content and determines the appropriate payment method
    based on additional content analysis.

    Supported payment methods:
    - MACRO_VISA: For Macro VISA credit card statements
    - MACRO_ACCOUNT: For Macro bank account statements
    """

    def can_detect(self, content: str) -> bool:
        """
        Check if this detector can identify Macro bank from content.

        Looks for Macro-specific indicators in the content to determine
        if this is a Macro bank statement.

        Args:
            content: Text content to analyze for Macro bank identification

        Returns:
            True if Macro bank indicators are found, False otherwise
        """
        if not content:
            return False

        content_upper = content.upper()
        indicators = [
            "MACRO PREMIA",
            "BANCO MACRO",
            "WWW.MACRO.COM.AR",
            "MACRO",  # More flexible matching for variations
        ]

        return any(indicator in content_upper for indicator in indicators)

    def get_payment_method(self, content: str) -> PaymentMethod:
        """
        Return the specific Macro payment method based on content analysis.

        Analyzes the content to determine if this is a VISA credit card
        statement or a bank account statement.

        Args:
            content: Text content to analyze for payment method identification

        Returns:
            PaymentMethod.MACRO_VISA for VISA statements,
            PaymentMethod.MACRO_ACCOUNT for account statements

        Raises:
            ValueError: If the specific payment method cannot be determined
        """
        if not content:
            raise ValueError("Content cannot be empty")

        content_upper = content.upper()

        # Check for VISA indicators
        if "VISA" in content_upper:
            return PaymentMethod.MACRO_VISA

        # Default to account for other Macro statements
        # This covers account statements and other non-VISA products
        return PaymentMethod.MACRO_ACCOUNT


class BBVADetector(BankDetector):
    """
    Concrete detector for BBVA bank statements.

    This detector identifies BBVA bank statements by looking for specific
    indicators in the content and determines the appropriate payment method
    based on additional content analysis.

    Supported payment methods:
    - BBVA_VISA: For BBVA VISA credit card statements
    - BBVA_MASTERCARD: For BBVA Mastercard credit card statements
    - BBVA_ACCOUNT: For BBVA bank account statements
    """

    def can_detect(self, content: str) -> bool:
        """
        Check if this detector can identify BBVA bank from content.

        Looks for BBVA-specific indicators in the content to determine
        if this is a BBVA bank statement.

        Args:
            content: Text content to analyze for BBVA bank identification

        Returns:
            True if BBVA bank indicators are found, False otherwise
        """
        if not content:
            return False

        content_upper = content.upper()
        bbva_indicators = [
            "BBVA",
            "WWW.BBVA.COM.AR",
        ]

        return any(indicator in content_upper for indicator in bbva_indicators)

    def get_payment_method(self, content: str) -> PaymentMethod:
        """
        Return the specific BBVA payment method based on content analysis.

        Analyzes the content to determine if this is a VISA credit card,
        Mastercard credit card, or bank account statement. Mastercard
        detection takes precedence over VISA when both are present.

        Args:
            content: Text content to analyze for payment method identification

        Returns:
            PaymentMethod.BBVA_MASTERCARD for Mastercard statements,
            PaymentMethod.BBVA_VISA for VISA statements,
            PaymentMethod.BBVA_ACCOUNT for account statements

        Raises:
            ValueError: If the specific payment method cannot be determined
        """
        if not content:
            raise ValueError("Content cannot be empty")

        content_upper = content.upper()

        # Check for Mastercard first (takes precedence over VISA)
        if "MASTERCARD" in content_upper:
            return PaymentMethod.BBVA_MASTERCARD

        # Check for VISA indicators
        if "VISA" in content_upper:
            return PaymentMethod.BBVA_VISA

        # Default to account for other BBVA statements
        # This covers account statements and other non-card products
        return PaymentMethod.BBVA_ACCOUNT


def build_default_payment_detector() -> PaymentMethodDetector:
    """
    Build a PaymentMethodDetector with all standard bank detectors registered.

    Creates a new PaymentMethodDetector instance and registers all available
    concrete bank detector implementations. This provides a convenient way
    to get a fully configured detector for standard usage.

    The detectors are registered in the following order:
    1. MacroDetector - for Macro bank statements
    2. BBVADetector - for BBVA bank statements

    Returns:
        PaymentMethodDetector instance with all standard detectors registered

    Example:
        >>> detector = build_default_payment_detector()
        >>> method = detector.detect_from_content("Banco Macro - Visa")
        >>> assert method == PaymentMethod.MACRO_VISA
        >>>
        >>> method = detector.detect_from_content("BBVA Mastercard")
        >>> assert method == PaymentMethod.BBVA_MASTERCARD
    """
    detector = PaymentMethodDetector()

    # Register all standard bank detectors
    detector.register_detector(MacroDetector())
    detector.register_detector(BBVADetector())

    return detector
