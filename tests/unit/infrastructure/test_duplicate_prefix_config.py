"""
Tests for configurable duplicate prefix functionality.

This module tests the duplicate prefix configuration feature across
the configuration loading, duplicate detection, and integration layers.
"""

import os
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from domain.models import Currency, PaymentMethod, Transaction
from domain.services import DuplicateDetector
from infrastructure.config import ApplicationConfig, ProcessingConfig


class TestDuplicatePrefixConfiguration:
    """Test duplicate prefix configuration functionality."""

    def test_processing_config_default_duplicate_prefix(self):
        """Test that ProcessingConfig has correct default duplicate prefix."""
        config = ProcessingConfig()
        assert config.duplicate_prefix == "DUPLICATED"

    def test_processing_config_custom_duplicate_prefix(self):
        """Test ProcessingConfig with custom duplicate prefix."""
        config = ProcessingConfig(duplicate_prefix="DUPLICADO")
        assert config.duplicate_prefix == "DUPLICADO"

    def test_duplicate_detector_default_prefix(self):
        """Test DuplicateDetector uses default prefix when not specified."""
        detector = DuplicateDetector()
        assert detector.duplicate_prefix == "DUPLICATED"

    def test_duplicate_detector_custom_prefix(self):
        """Test DuplicateDetector uses custom prefix when specified."""
        detector = DuplicateDetector("DUPLICADO")
        assert detector.duplicate_prefix == "DUPLICADO"

    def test_duplicate_detector_marks_with_custom_prefix(self):
        """Test that DuplicateDetector marks duplicates with custom prefix."""
        # Create test transactions
        transaction1 = Transaction(
            date=date(2025, 4, 2),
            description="Test Transaction",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="REF1",
        )

        transaction2 = Transaction(
            date=date(2025, 4, 2),
            description="Another Transaction",
            amount=Decimal("100.00"),  # Same amount and date
            currency=Currency.ARS,
            payment_method=PaymentMethod.MACRO_VISA,
            reference="REF2",
        )

        # Test with custom prefix
        detector = DuplicateDetector("DUPLICADO")
        result_transactions, duplicate_count = detector.mark_duplicates(
            [transaction1, transaction2]
        )

        assert len(result_transactions) == 2
        assert duplicate_count == 1
        assert result_transactions[0].description == "Test Transaction"
        assert result_transactions[1].description == "DUPLICADO: Another Transaction"

    def test_duplicate_detector_marks_with_different_languages(self):
        """Test duplicate detection with various language prefixes."""
        transaction1 = Transaction(
            date=date(2025, 4, 2),
            description="Original Transaction",
            amount=Decimal("50.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="ORIG",
        )

        transaction2 = Transaction(
            date=date(2025, 4, 2),
            description="Duplicate Transaction",
            amount=Decimal("50.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MACRO_VISA,
            reference="DUP",
        )

        test_cases = [
            ("DUPLICADO", "DUPLICADO: Duplicate Transaction"),  # Spanish
            ("DUPLIQUÉ", "DUPLIQUÉ: Duplicate Transaction"),  # French
            ("DUPLICATE", "DUPLICATE: Duplicate Transaction"),  # English alternative
            ("重复", "重复: Duplicate Transaction"),  # Chinese
        ]

        for prefix, expected_description in test_cases:
            detector = DuplicateDetector(prefix)
            result_transactions, duplicate_count = detector.mark_duplicates(
                [transaction1, transaction2]
            )

            assert len(result_transactions) == 2
            assert duplicate_count == 1
            assert result_transactions[1].description == expected_description

    def test_yaml_configuration_loading_duplicate_prefix(self):
        """Test loading duplicate prefix from YAML configuration."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
processing:
  duplicate_prefix: "DUPLICADO"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                config = ApplicationConfig.from_yaml(Path(f.name))
                assert config.processing.duplicate_prefix == "DUPLICADO"
            finally:
                os.unlink(f.name)

    def test_yaml_configuration_default_duplicate_prefix(self):
        """Test that YAML configuration uses default when prefix not specified."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
processing:
  max_workers: 4
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                config = ApplicationConfig.from_yaml(Path(f.name))
                assert config.processing.duplicate_prefix == "DUPLICATED"
            finally:
                os.unlink(f.name)

    def test_environment_variable_duplicate_prefix(self):
        """Test loading duplicate prefix from environment variable."""
        # Set environment variable
        os.environ["FSP_DUPLICATE_PREFIX"] = "DUPLICADO"

        try:
            config = ApplicationConfig.from_environment()
            assert config.processing.duplicate_prefix == "DUPLICADO"
        finally:
            # Clean up environment variable
            if "FSP_DUPLICATE_PREFIX" in os.environ:
                del os.environ["FSP_DUPLICATE_PREFIX"]

    def test_environment_variable_default_duplicate_prefix(self):
        """Test that environment configuration uses default when variable not set."""
        # Ensure environment variable is not set
        if "FSP_DUPLICATE_PREFIX" in os.environ:
            del os.environ["FSP_DUPLICATE_PREFIX"]

        config = ApplicationConfig.from_environment()
        assert config.processing.duplicate_prefix == "DUPLICATED"

    def test_yaml_configuration_precedence_over_default(self):
        """Test that YAML configuration overrides default values."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
processing:
  duplicate_prefix: "YAML_PREFIX"
  max_workers: 8
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                config = ApplicationConfig.from_yaml(Path(f.name))
                assert config.processing.duplicate_prefix == "YAML_PREFIX"
                assert config.processing.max_workers == 8
            finally:
                os.unlink(f.name)

    def test_mercadopago_pattern_with_custom_prefix(self):
        """Test MercadoPago duplicate pattern with custom prefix."""
        # Create the MercadoPago pattern with custom prefix
        macro_visa = Transaction(
            date=date(2025, 4, 2),
            description="789797K MERPAGO*VILLACRESPO",
            amount=Decimal("15500.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MACRO_VISA,
            reference="789797K",
        )

        mp_ingreso = Transaction(
            date=date(2025, 4, 2),
            description="Ingreso de dinero",
            amount=Decimal("15500.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MERCADOPAGO,
            reference="MP_IN",
        )

        mp_pago = Transaction(
            date=date(2025, 4, 2),
            description="Pago",
            amount=Decimal("-15500.00"),  # Negative amount
            currency=Currency.ARS,
            payment_method=PaymentMethod.MERCADOPAGO,
            reference="MP_OUT",
        )

        detector = DuplicateDetector("DUPLICADO")
        result_transactions, duplicate_count = detector.mark_duplicates(
            [macro_visa, mp_ingreso, mp_pago]
        )

        assert len(result_transactions) == 3
        assert duplicate_count == 2

        # Verify custom prefix is used
        duplicated_descriptions = [
            t.description
            for t in result_transactions
            if t.description.startswith("DUPLICADO:")
        ]
        assert len(duplicated_descriptions) == 2
        assert "DUPLICADO: Ingreso de dinero" in duplicated_descriptions
        assert "DUPLICADO: Pago" in duplicated_descriptions

    def test_empty_duplicate_prefix(self):
        """Test handling of empty duplicate prefix."""
        detector = DuplicateDetector("")

        transaction1 = Transaction(
            date=date(2025, 1, 1),
            description="Transaction 1",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="T1",
        )

        transaction2 = Transaction(
            date=date(2025, 1, 1),
            description="Transaction 2",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="T2",
        )

        result_transactions, duplicate_count = detector.mark_duplicates(
            [transaction1, transaction2]
        )

        assert len(result_transactions) == 2
        assert duplicate_count == 1
        assert result_transactions[1].description == ": Transaction 2"

    def test_special_characters_in_prefix(self):
        """Test duplicate prefix with special characters."""
        special_prefixes = [
            "⚠️ DUPLICATE",
            "[DUPLICATE]",
            ">>> DUPLICATE <<<",
            "DUPLICATE-WARNING",
        ]

        for prefix in special_prefixes:
            detector = DuplicateDetector(prefix)

            transaction1 = Transaction(
                date=date(2025, 1, 1),
                description="Original",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
                reference="ORIG",
            )

            transaction2 = Transaction(
                date=date(2025, 1, 1),
                description="Duplicate",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
                reference="DUP",
            )

            result_transactions, duplicate_count = detector.mark_duplicates(
                [transaction1, transaction2]
            )

            assert len(result_transactions) == 2
            assert duplicate_count == 1
            assert result_transactions[1].description == f"{prefix}: Duplicate"
