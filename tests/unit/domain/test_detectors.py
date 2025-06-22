"""
Unit tests for the PaymentMethodDetector and BankDetector classes.

This module tests the payment method detection abstractions including
the Strategy Pattern implementation and registry-based detector system.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from domain.detectors import BankDetector, PaymentMethodDetector
from domain.models import PaymentMethod


class TestBankDetector:
    """Unit tests for BankDetector abstract base class"""

    def test_bank_detector_is_abstract(self):
        """Test that BankDetector cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BankDetector()

    def test_bank_detector_subclass_validation(self):
        """Test that proper subclasses can be created"""

        class ConcreteBankDetector(BankDetector):
            def can_detect(self, content: str) -> bool:
                return True

            def get_payment_method(self, content: str) -> PaymentMethod:
                return PaymentMethod.MACRO_VISA

        # Should be able to create concrete implementation
        detector = ConcreteBankDetector()
        assert isinstance(detector, BankDetector)
        assert detector.can_detect("test")
        assert detector.get_payment_method("test") == PaymentMethod.MACRO_VISA

    def test_incomplete_subclass_fails(self):
        """Test that incomplete subclasses cannot be instantiated"""

        class IncompleteBankDetector(BankDetector):
            def can_detect(self, content: str) -> bool:
                return True

            # Missing get_payment_method implementation

        with pytest.raises(TypeError):
            IncompleteBankDetector()


class TestPaymentMethodDetector:
    """Unit tests for PaymentMethodDetector class"""

    def test_detector_initialization(self):
        """Test detector initializes with empty registry"""
        detector = PaymentMethodDetector()
        assert len(detector.get_registered_detectors()) == 0

    def test_register_detector_valid(self):
        """Test registering valid BankDetector implementation"""
        detector = PaymentMethodDetector()
        mock_bank_detector = Mock(spec=BankDetector)

        detector.register_detector(mock_bank_detector)

        registered = detector.get_registered_detectors()
        assert len(registered) == 1
        assert registered[0] is mock_bank_detector

    def test_register_detector_invalid_type(self):
        """Test registering invalid detector type raises TypeError"""
        detector = PaymentMethodDetector()

        with pytest.raises(TypeError, match="Expected BankDetector, got str"):
            detector.register_detector("not a detector")

        with pytest.raises(TypeError, match="Expected BankDetector, got int"):
            detector.register_detector(123)

    def test_register_multiple_detectors(self):
        """Test registering multiple detectors maintains order"""
        detector = PaymentMethodDetector()
        mock_detector1 = Mock(spec=BankDetector)
        mock_detector2 = Mock(spec=BankDetector)

        detector.register_detector(mock_detector1)
        detector.register_detector(mock_detector2)

        registered = detector.get_registered_detectors()
        assert len(registered) == 2
        assert registered[0] is mock_detector1
        assert registered[1] is mock_detector2

    def test_detect_from_content_no_detectors_registered(self):
        """Test detect_from_content raises ValueError when no detectors registered"""
        detector = PaymentMethodDetector()

        with pytest.raises(ValueError, match="No detectors registered"):
            detector.detect_from_content("BANCO MACRO VISA")

    def test_detect_from_content_empty_content(self):
        """Test detect_from_content raises ValueError for empty content"""
        detector = PaymentMethodDetector()
        mock_bank_detector = Mock(spec=BankDetector)
        detector.register_detector(mock_bank_detector)

        with pytest.raises(ValueError, match="Content cannot be empty"):
            detector.detect_from_content("")

        with pytest.raises(ValueError, match="Content cannot be empty"):
            detector.detect_from_content("   ")

    def test_detect_from_content_successful_detection(self):
        """Test successful payment method detection from content"""
        detector = PaymentMethodDetector()
        mock_bank_detector = Mock(spec=BankDetector)
        mock_bank_detector.can_detect.return_value = True
        mock_bank_detector.get_payment_method.return_value = PaymentMethod.MACRO_VISA

        detector.register_detector(mock_bank_detector)

        result = detector.detect_from_content("BANCO MACRO VISA")

        assert result == PaymentMethod.MACRO_VISA
        mock_bank_detector.can_detect.assert_called_once_with("BANCO MACRO VISA")
        mock_bank_detector.get_payment_method.assert_called_once_with(
            "BANCO MACRO VISA"
        )

    def test_detect_from_content_first_match_wins(self):
        """Test that first matching detector is used"""
        detector = PaymentMethodDetector()

        mock_detector1 = Mock(spec=BankDetector)
        mock_detector1.can_detect.return_value = True
        mock_detector1.get_payment_method.return_value = PaymentMethod.MACRO_VISA

        mock_detector2 = Mock(spec=BankDetector)
        mock_detector2.can_detect.return_value = True
        mock_detector2.get_payment_method.return_value = PaymentMethod.BBVA_VISA

        detector.register_detector(mock_detector1)
        detector.register_detector(mock_detector2)

        result = detector.detect_from_content("BANCO MACRO VISA")

        assert result == PaymentMethod.MACRO_VISA
        mock_detector1.can_detect.assert_called_once_with("BANCO MACRO VISA")
        mock_detector1.get_payment_method.assert_called_once_with("BANCO MACRO VISA")
        # Second detector should not be called since first one matched
        mock_detector2.can_detect.assert_not_called()
        mock_detector2.get_payment_method.assert_not_called()

    def test_detect_from_content_no_match_found(self):
        """Test detect_from_content raises ValueError when no detector matches"""
        detector = PaymentMethodDetector()

        mock_detector1 = Mock(spec=BankDetector)
        mock_detector1.can_detect.return_value = False

        mock_detector2 = Mock(spec=BankDetector)
        mock_detector2.can_detect.return_value = False

        detector.register_detector(mock_detector1)
        detector.register_detector(mock_detector2)

        with pytest.raises(ValueError, match="Unknown payment method"):
            detector.detect_from_content("UNKNOWN BANK")

        # Both detectors should be consulted
        mock_detector1.can_detect.assert_called_once_with("UNKNOWN BANK")
        mock_detector2.can_detect.assert_called_once_with("UNKNOWN BANK")

    def test_detect_from_filename_invalid_path_type(self):
        """Test detect_from_filename raises TypeError for invalid path type"""
        detector = PaymentMethodDetector()

        with pytest.raises(TypeError, match="Expected Path, got str"):
            detector.detect_from_filename("not_a_path.pdf")

    def test_detect_from_filename_bbva_visa_csv(self):
        """Test detection of BBVA VISA from CSV filename"""
        detector = PaymentMethodDetector()

        test_paths = [
            Path("BBVA-Visa-Autorizaciones.csv"),
            Path("bbva-visa-movimientos.csv"),
            Path("VISA-BBVA-statements.csv"),
        ]

        for path in test_paths:
            result = detector.detect_from_filename(path)
            assert result == PaymentMethod.BBVA_VISA

    def test_detect_from_filename_macro_visa_csv(self):
        """Test detection of Macro VISA from CSV filename"""
        detector = PaymentMethodDetector()

        test_paths = [
            Path("MACRO-Visa-Autorizaciones.csv"),
            Path("macro-visa-movimientos.csv"),
            Path("VISA-MACRO-statements.csv"),
        ]

        for path in test_paths:
            result = detector.detect_from_filename(path)
            assert result == PaymentMethod.MACRO_VISA

    def test_detect_from_filename_bbva_account_xls(self):
        """Test detection of BBVA Account from XLS filename"""
        detector = PaymentMethodDetector()

        test_paths = [
            Path("BBVA-Account-Detalle_mov_cuenta.xls"),
            Path("bbva-detalle-movimientos.xls"),
            Path("DETALLE-BBVA-account.xls"),
        ]

        for path in test_paths:
            result = detector.detect_from_filename(path)
            assert result == PaymentMethod.BBVA_ACCOUNT

    def test_detect_from_filename_macro_account_xls(self):
        """Test detection of Macro Account from XLS filename"""
        detector = PaymentMethodDetector()

        test_paths = [
            Path("MACRO-movimientos-de-cuenta.xls"),
            Path("macro-movimientos-statement.xls"),
            Path("MOVIMIENTOS-MACRO-account.xls"),
        ]

        for path in test_paths:
            result = detector.detect_from_filename(path)
            assert result == PaymentMethod.MACRO_ACCOUNT

    def test_detect_from_filename_mercadopago_xlsx(self):
        """Test detection of Mercadopago from XLSX filename"""
        detector = PaymentMethodDetector()

        test_paths = [
            Path("mercadopago.xlsx"),
            Path("MERCADOPAGO-2025.xlsx"),
            Path("mercadopago-transactions.xlsx"),
        ]

        for path in test_paths:
            result = detector.detect_from_filename(path)
            assert result == PaymentMethod.MERCADOPAGO

    def test_detect_from_filename_unknown_pattern(self):
        """Test detect_from_filename raises ValueError for unknown patterns"""
        detector = PaymentMethodDetector()

        unknown_paths = [
            Path("santander-visa.csv"),
            Path("unknown-bank.xls"),
            Path("random-file.xlsx"),
            Path("statement.pdf"),  # PDF not supported by filename detection
        ]

        for path in unknown_paths:
            with pytest.raises(ValueError, match="Unknown payment method for file"):
                detector.detect_from_filename(path)

    def test_get_registered_detectors_returns_copy(self):
        """Test get_registered_detectors returns a copy to prevent external modification"""
        detector = PaymentMethodDetector()
        mock_bank_detector = Mock(spec=BankDetector)
        detector.register_detector(mock_bank_detector)

        registered1 = detector.get_registered_detectors()
        registered2 = detector.get_registered_detectors()

        # Should be different list objects
        assert registered1 is not registered2
        # But contain the same detectors
        assert registered1 == registered2
        assert len(registered1) == 1
        assert registered1[0] is mock_bank_detector

        # Modifying returned list should not affect internal registry
        registered1.clear()
        registered3 = detector.get_registered_detectors()
        assert len(registered3) == 1

    def test_clear_detectors(self):
        """Test clear_detectors removes all registered detectors"""
        detector = PaymentMethodDetector()
        mock_detector1 = Mock(spec=BankDetector)
        mock_detector2 = Mock(spec=BankDetector)

        detector.register_detector(mock_detector1)
        detector.register_detector(mock_detector2)
        assert len(detector.get_registered_detectors()) == 2

        detector.clear_detectors()
        assert len(detector.get_registered_detectors()) == 0

        # Should raise ValueError since no detectors are registered
        with pytest.raises(ValueError, match="No detectors registered"):
            detector.detect_from_content("test content")


class TestPaymentMethodDetectorIntegration:
    """Integration tests for PaymentMethodDetector with concrete implementations"""

    def test_integration_with_concrete_detectors(self):
        """Test PaymentMethodDetector with concrete BankDetector implementations"""

        class MacroDetector(BankDetector):
            def can_detect(self, content: str) -> bool:
                indicators = ["MACRO PREMIA", "BANCO MACRO"]
                return any(indicator in content.upper() for indicator in indicators)

            def get_payment_method(self, content: str) -> PaymentMethod:
                if "VISA" in content.upper():
                    return PaymentMethod.MACRO_VISA
                return PaymentMethod.MACRO_ACCOUNT

        class BBVADetector(BankDetector):
            def can_detect(self, content: str) -> bool:
                indicators = ["BBVA", "WWW.BBVA.COM.AR"]
                return any(indicator in content.upper() for indicator in indicators)

            def get_payment_method(self, content: str) -> PaymentMethod:
                content_upper = content.upper()
                if "MASTERCARD" in content_upper:
                    return PaymentMethod.BBVA_MASTERCARD
                elif "VISA" in content_upper:
                    return PaymentMethod.BBVA_VISA
                return PaymentMethod.BBVA_ACCOUNT

        detector = PaymentMethodDetector()
        detector.register_detector(MacroDetector())
        detector.register_detector(BBVADetector())

        # Test Macro VISA detection
        result = detector.detect_from_content("BANCO MACRO VISA SIGNATURE")
        assert result == PaymentMethod.MACRO_VISA

        # Test BBVA Mastercard detection
        result = detector.detect_from_content("BBVA MASTERCARD BLACK")
        assert result == PaymentMethod.BBVA_MASTERCARD

        # Test BBVA VISA detection
        result = detector.detect_from_content("BBVA VISA SIGNATURE")
        assert result == PaymentMethod.BBVA_VISA

        # Test unknown bank
        with pytest.raises(ValueError, match="Unknown payment method"):
            detector.detect_from_content("SANTANDER VISA")

    def test_detector_precedence_order(self):
        """Test that detector registration order determines precedence"""

        class FirstDetector(BankDetector):
            def can_detect(self, content: str) -> bool:
                return "BANK" in content.upper()

            def get_payment_method(self, content: str) -> PaymentMethod:
                return PaymentMethod.MACRO_VISA

        class SecondDetector(BankDetector):
            def can_detect(self, content: str) -> bool:
                return "BANK" in content.upper()

            def get_payment_method(self, content: str) -> PaymentMethod:
                return PaymentMethod.BBVA_VISA

        detector = PaymentMethodDetector()
        detector.register_detector(FirstDetector())
        detector.register_detector(SecondDetector())

        # First detector should win
        result = detector.detect_from_content("BANK STATEMENT")
        assert result == PaymentMethod.MACRO_VISA

        # Clear and register in reverse order
        detector.clear_detectors()
        detector.register_detector(SecondDetector())
        detector.register_detector(FirstDetector())

        # Second detector should now win (registered first)
        result = detector.detect_from_content("BANK STATEMENT")
        assert result == PaymentMethod.BBVA_VISA
