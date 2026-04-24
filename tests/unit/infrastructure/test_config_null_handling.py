"""
Tests for configuration null value handling.

This module tests the configuration system's ability to handle null values
gracefully, particularly for payment method mapping configuration.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from domain.models import PaymentMethod
from infrastructure.config import ApplicationConfig, PaymentMethodMappingConfig


class TestConfigurationNullHandling:
    """Test configuration null value handling."""

    def test_payment_method_mapping_config_with_none_mappings(self):
        """Test PaymentMethodMappingConfig handles None mappings gracefully."""
        # This should not crash - the dataclass default factory should handle it
        config = PaymentMethodMappingConfig()

        # Should return default enum values
        assert config.get_display_name(PaymentMethod.BBVA_VISA) == "BBVA Visa"
        assert config.get_display_name(PaymentMethod.MACRO_VISA) == "Macro Visa"
        assert config.get_display_name(PaymentMethod.MERCADOPAGO) == "Mercado Pago"

    def test_yaml_config_with_null_payment_method_mapping(self):
        """Test YAML configuration with explicit null payment method mapping."""
        yaml_content = {
            "input_directory": "test_input",
            "output_directory": "test_output",
            "payment_method_mapping": None,  # Explicit null
            "processing": {"max_workers": 2, "enable_validation": True},
            "output": {"decimal_separator": "."},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            config_path = Path(f.name)

        try:
            # This should not crash with the fix
            config = ApplicationConfig.from_yaml(config_path)

            # Verify the payment method mapping was created with empty mappings
            assert config.payment_method_mapping is not None
            assert config.payment_method_mapping.mappings == {}

            # Verify it returns default enum values
            assert (
                config.payment_method_mapping.get_display_name(PaymentMethod.BBVA_VISA)
                == "BBVA Visa"
            )
            assert (
                config.payment_method_mapping.get_display_name(PaymentMethod.MACRO_VISA)
                == "Macro Visa"
            )
            assert (
                config.payment_method_mapping.get_display_name(
                    PaymentMethod.MERCADOPAGO
                )
                == "Mercado Pago"
            )

            # Verify other configurations still work
            assert config.processing.max_workers == 2
            assert config.output.decimal_separator == "."

        finally:
            config_path.unlink()  # Clean up

    def test_yaml_config_with_missing_payment_method_mapping(self):
        """Test YAML configuration with missing payment method mapping section."""
        yaml_content = {
            "input_directory": "test_input",
            "output_directory": "test_output",
            # payment_method_mapping is completely missing
            "processing": {"max_workers": 4},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            config_path = Path(f.name)

        try:
            config = ApplicationConfig.from_yaml(config_path)

            # Should use default empty mappings
            assert config.payment_method_mapping is not None
            assert config.payment_method_mapping.mappings == {}

            # Should return default enum values
            assert (
                config.payment_method_mapping.get_display_name(PaymentMethod.BBVA_VISA)
                == "BBVA Visa"
            )

        finally:
            config_path.unlink()

    def test_yaml_config_with_empty_payment_method_mapping(self):
        """Test YAML configuration with empty payment method mapping."""
        yaml_content = {
            "input_directory": "test_input",
            "output_directory": "test_output",
            "payment_method_mapping": {},  # Explicit empty dict
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            config_path = Path(f.name)

        try:
            config = ApplicationConfig.from_yaml(config_path)

            # Should work with empty mappings
            assert config.payment_method_mapping is not None
            assert config.payment_method_mapping.mappings == {}

            # Should return default enum values
            assert (
                config.payment_method_mapping.get_display_name(PaymentMethod.BBVA_VISA)
                == "BBVA Visa"
            )

        finally:
            config_path.unlink()

    def test_yaml_config_with_valid_payment_method_mapping(self):
        """Test YAML configuration with valid payment method mapping."""
        yaml_content = {
            "input_directory": "test_input",
            "output_directory": "test_output",
            "payment_method_mapping": {
                "BBVA_VISA": "BBVA VISA CUSTOM",
                "MACRO_VISA": "MACRO VISA CUSTOM",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            config_path = Path(f.name)

        try:
            config = ApplicationConfig.from_yaml(config_path)

            # Should use custom mappings
            assert (
                config.payment_method_mapping.get_display_name(PaymentMethod.BBVA_VISA)
                == "BBVA VISA CUSTOM"
            )
            assert (
                config.payment_method_mapping.get_display_name(PaymentMethod.MACRO_VISA)
                == "MACRO VISA CUSTOM"
            )

            # Should use default for unmapped methods
            assert (
                config.payment_method_mapping.get_display_name(
                    PaymentMethod.MERCADOPAGO
                )
                == "Mercado Pago"
            )

        finally:
            config_path.unlink()

    def test_environment_config_payment_method_mapping_defaults(self):
        """Test environment configuration with no payment method mapping variables."""
        # Test with clean environment
        with patch.dict("os.environ", {}, clear=True):
            # Add only required environment variables
            with patch.dict(
                "os.environ",
                {"FSP_INPUT_DIR": "test_input", "FSP_OUTPUT_DIR": "test_output"},
            ):
                config = ApplicationConfig.from_environment()

                # Should create empty mappings
                assert config.payment_method_mapping is not None
                assert config.payment_method_mapping.mappings == {}

                # Should return default enum values
                assert (
                    config.payment_method_mapping.get_display_name(
                        PaymentMethod.BBVA_VISA
                    )
                    == "BBVA Visa"
                )

    def test_regression_original_error_scenario(self):
        """Test the exact scenario that caused the original error."""
        # This simulates the exact YAML content that caused the bug
        yaml_content = """
input_directory: "input"
output_directory: "output"
log_level: "DEBUG"

processing:
  max_workers: 2
  retry_attempts: 2
  enable_validation: true
  enable_balance_checking: true

output:
  default_format: "excel"
  date_format: "%Y-%m-%d"
  decimal_separator: ","

payment_method_mapping: null
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            config_path = Path(f.name)

        try:
            # This should not crash after our fix
            config = ApplicationConfig.from_yaml(config_path)

            # Verify payment method mapping is properly initialized
            assert config.payment_method_mapping is not None
            assert config.payment_method_mapping.mappings == {}

            # Verify get_display_name works correctly
            display_name = config.payment_method_mapping.get_display_name(
                PaymentMethod.BBVA_VISA
            )
            assert display_name == "BBVA Visa"

            # This call should not raise "'NoneType' object has no attribute 'get'"
            # Simulate the repository usage that was failing
            for payment_method in PaymentMethod:
                display_name = config.payment_method_mapping.get_display_name(
                    payment_method
                )
                assert display_name == payment_method.value
                assert isinstance(display_name, str)
                assert len(display_name) > 0

        finally:
            config_path.unlink()
