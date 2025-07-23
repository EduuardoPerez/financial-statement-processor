"""
Tests for decimal separator configuration functionality.

This module tests the configuration system's ability to handle decimal
separator settings through YAML files and environment variables.
"""

import os
import tempfile
from pathlib import Path

from infrastructure.config import ApplicationConfig, OutputConfig


class TestDecimalSeparatorConfiguration:
    """Test decimal separator configuration functionality."""

    def test_output_config_default_decimal_separator(self):
        """Test OutputConfig has default decimal separator."""
        config = OutputConfig()
        assert config.decimal_separator == ","

    def test_output_config_custom_decimal_separator(self):
        """Test OutputConfig accepts custom decimal separator."""
        config = OutputConfig(decimal_separator=".")
        assert config.decimal_separator == "."

    def test_yaml_configuration_with_decimal_separator(self):
        """Test loading decimal separator from YAML configuration."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
output:
  decimal_separator: "."
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            config_path = Path(f.name)

        try:
            config = ApplicationConfig.from_yaml(config_path)
            assert config.output.decimal_separator == "."
        finally:
            config_path.unlink()

    def test_yaml_configuration_without_decimal_separator(self):
        """Test loading YAML configuration uses default decimal separator."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
output:
  default_format: "excel"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            config_path = Path(f.name)

        try:
            config = ApplicationConfig.from_yaml(config_path)
            assert config.output.decimal_separator == ","
        finally:
            config_path.unlink()

    def test_environment_variable_decimal_separator(self):
        """Test loading decimal separator from environment variable."""
        # Set environment variable
        os.environ["FSP_DECIMAL_SEPARATOR"] = "."

        try:
            config = ApplicationConfig.from_environment()
            assert config.output.decimal_separator == "."
        finally:
            # Clean up environment variable
            if "FSP_DECIMAL_SEPARATOR" in os.environ:
                del os.environ["FSP_DECIMAL_SEPARATOR"]

    def test_environment_variable_default_decimal_separator(self):
        """Test environment configuration uses default decimal separator."""
        # Ensure environment variable is not set
        if "FSP_DECIMAL_SEPARATOR" in os.environ:
            del os.environ["FSP_DECIMAL_SEPARATOR"]

        config = ApplicationConfig.from_environment()
        assert config.output.decimal_separator == ","

    def test_decimal_separator_validation_options(self):
        """Test different valid decimal separator options."""
        valid_separators = [",", ".", ";"]

        for separator in valid_separators:
            config = OutputConfig(decimal_separator=separator)
            assert config.decimal_separator == separator
