"""
Payment method detection abstractions for the Financial Statement Processor.

This module defines abstract detector interfaces and concrete detector registry
that form the core payment method identification logic in our hexagonal
architecture. These abstractions enable the Strategy Pattern for different
bank detection implementations.

Classes:
    BankDetector: Abstract strategy for bank identification
    PaymentMethodDetector: Registry-based detector with registration and
                          detection methods
"""

from abc import ABC, abstractmethod
from pathlib import Path

from .models import PaymentMethod


class BankDetector(ABC):
    """
    Abstract strategy for bank identification from content.

    This abstract base class defines the contract that all concrete bank
    detectors must implement. It enables the Strategy Pattern for handling
    different bank identification logic in a pluggable manner.

    The detector is responsible for:
    1. Determining if it can identify a specific bank from content
    2. Returning the appropriate PaymentMethod for the identified bank

    Example:
        >>> class MacroDetector(BankDetector):
        ...     def can_detect(self, content: str) -> bool:
        ...         indicators = ["MACRO PREMIA", "BANCO MACRO"]
        ...         return any(indicator in content.upper()
        ...                    for indicator in indicators)
        ...
        ...     def get_payment_method(self, content: str) -> PaymentMethod:
        ...         if "VISA" in content.upper():
        ...             return PaymentMethod.MACRO_VISA
        ...         return PaymentMethod.MACRO_ACCOUNT
        >>>
        >>> detector = MacroDetector()
        >>> assert issubclass(MacroDetector, BankDetector)
    """

    @abstractmethod
    def can_detect(self, content: str) -> bool:
        """
        Check if this detector can identify the bank from content.

        This method should examine the content to determine if this specific
        detector implementation can identify the bank and payment method.

        Args:
            content: Text content to analyze for bank identification

        Returns:
            True if this detector can identify the bank, False otherwise

        Example:
            >>> detector = SomeConcreteDetector()
            >>> can_identify = detector.can_detect("BANCO MACRO VISA")
            >>> print(f"Can detect: {can_identify}")
        """
        raise NotImplementedError

    @abstractmethod
    def get_payment_method(self, content: str) -> PaymentMethod:
        """
        Return the specific payment method for the identified bank.

        This method should only be called after can_detect() returns True.
        It analyzes the content to determine the specific payment method
        (e.g., VISA vs Mastercard vs Account).

        Args:
            content: Text content to analyze for payment method identification

        Returns:
            PaymentMethod enum value for the identified payment method

        Raises:
            ValueError: If the payment method cannot be determined

        Example:
            >>> detector = SomeConcreteDetector()
            >>> if detector.can_detect(content):
            ...     method = detector.get_payment_method(content)
            ...     print(f"Detected: {method.value}")
        """
        raise NotImplementedError


class PaymentMethodDetector:
    """
    Registry-based payment method detector following Strategy Pattern.

    This class manages a collection of BankDetector strategies and provides
    methods for registering new detectors and detecting payment methods from
    content or filenames. It follows the Open/Closed Principle by allowing
    new bank detectors to be added without modifying existing code.

    The detector supports:
    1. Registration of new bank detection strategies
    2. Content-based detection using registered detectors
    3. Filename-based detection for structured file naming patterns
    4. Validation that detectors are registered before detection

    Example:
        >>> detector = PaymentMethodDetector()
        >>> detector.register_detector(MacroDetector())
        >>> detector.register_detector(BBVADetector())
        >>>
        >>> method = detector.detect_from_content("BANCO MACRO VISA")
        >>> print(f"Detected: {method.value}")
    """

    def __init__(self) -> None:
        """Initialize detector with empty registry."""
        self._detectors: list[BankDetector] = []

    def register_detector(self, detector: object) -> None:
        """
        Register a new bank detector strategy.

        Adds a new BankDetector implementation to the registry. The detector
        will be consulted in registration order when detecting payment methods.

        Args:
            detector: BankDetector implementation to register

        Raises:
            TypeError: If detector is not a BankDetector instance

        Example:
            >>> detector_registry = PaymentMethodDetector()
            >>> macro_detector = MacroDetector()
            >>> detector_registry.register_detector(macro_detector)
        """
        if not isinstance(detector, BankDetector):
            raise TypeError(f"Expected BankDetector, got {type(detector).__name__}")

        self._detectors.append(detector)

    def detect_from_content(self, content: str) -> PaymentMethod:
        """
        Detect payment method from content using registered detectors.

        Iterates through registered detectors in registration order and returns
        the payment method from the first detector that can identify the bank.

        Args:
            content: Text content to analyze for payment method identification

        Returns:
            PaymentMethod enum value for the identified payment method

        Raises:
            ValueError: If no detectors are registered or no detector can
                       identify the bank

        Example:
            >>> detector = PaymentMethodDetector()
            >>> detector.register_detector(MacroDetector())
            >>> method = detector.detect_from_content("BANCO MACRO VISA")
            >>> assert method == PaymentMethod.MACRO_VISA
        """
        if not self._detectors:
            msg = "No detectors registered. Cannot detect payment method."
            raise ValueError(msg)

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        for detector in self._detectors:
            if detector.can_detect(content):
                return detector.get_payment_method(content)

        raise ValueError("Unknown payment method")

    def detect_from_filename(self, file_path: Path) -> PaymentMethod:
        """
        Detect payment method from filename patterns.

        Analyzes the filename and extension to determine the payment method
        based on established naming conventions for different file types.

        Args:
            file_path: Path to the file for payment method detection

        Returns:
            PaymentMethod enum value for the identified payment method

        Raises:
            ValueError: If the filename pattern is not recognized

        Example:
            >>> detector = PaymentMethodDetector()
            >>> path = Path("BBVA-Account-statement.xls")
            >>> method = detector.detect_from_filename(path)
            >>> assert method == PaymentMethod.BBVA_ACCOUNT
        """
        if not isinstance(file_path, Path):
            raise TypeError(f"Expected Path, got {type(file_path).__name__}")

        filename_upper = file_path.name.upper()
        extension = file_path.suffix.lower()

        # CSV filename-based detection
        if extension == ".csv":
            bbva_visa_keywords = ["BBVA", "VISA"]
            macro_visa_keywords = ["MACRO", "VISA"]
            if all(keyword in filename_upper for keyword in bbva_visa_keywords):
                return PaymentMethod.BBVA_VISA
            elif all(keyword in filename_upper for keyword in macro_visa_keywords):
                return PaymentMethod.MACRO_VISA

        # XLS filename-based detection
        elif extension == ".xls":
            bbva_account_keywords_1 = ["BBVA", "DETALLE"]
            bbva_account_keywords_2 = ["BBVA", "MOVIMIENTOS"]
            bbva_account_keywords_3 = ["BBVA", "ACCOUNT"]
            macro_account_keywords_1 = ["MACRO", "DETALLE"]
            macro_account_keywords_2 = ["MACRO", "MOVIMIENTOS"]
            macro_account_keywords_3 = ["MACRO", "ACCOUNT"]
            if (
                all(keyword in filename_upper for keyword in bbva_account_keywords_1)
                or all(keyword in filename_upper for keyword in bbva_account_keywords_2)
                or all(keyword in filename_upper for keyword in bbva_account_keywords_3)
            ):
                return PaymentMethod.BBVA_ACCOUNT
            elif (
                all(keyword in filename_upper for keyword in macro_account_keywords_1)
                or all(
                    keyword in filename_upper for keyword in macro_account_keywords_2
                )
                or all(
                    keyword in filename_upper for keyword in macro_account_keywords_3
                )
            ):
                return PaymentMethod.MACRO_ACCOUNT

        # XLSX filename-based detection
        elif extension == ".xlsx":
            if "MERCADOPAGO" in filename_upper:
                return PaymentMethod.MERCADOPAGO
            elif "BBVA" in filename_upper and "MASTERCARD" in filename_upper:
                return PaymentMethod.BBVA_MASTERCARD

        raise ValueError(f"Unknown payment method for file: {file_path}")

    def get_registered_detectors(self) -> list[BankDetector]:
        """
        Get a copy of all registered detectors.

        Returns a copy of the internal detector list to prevent external
        modification while allowing inspection of registered detectors.

        Returns:
            List of registered BankDetector instances

        Example:
            >>> detector = PaymentMethodDetector()
            >>> detector.register_detector(MacroDetector())
            >>> detectors = detector.get_registered_detectors()
            >>> print(f"Registered detectors: {len(detectors)}")
        """
        return self._detectors.copy()

    def clear_detectors(self) -> None:
        """
        Remove all registered detectors.

        Clears the internal detector registry. Useful for testing scenarios
        or when reconfiguring the detector with a different set of strategies.

        Example:
            >>> detector = PaymentMethodDetector()
            >>> detector.register_detector(MacroDetector())
            >>> detector.clear_detectors()
            >>> assert len(detector.get_registered_detectors()) == 0
        """
        self._detectors.clear()
