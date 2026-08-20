import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from src.infrastructure.config import (
    ApplicationConfig,
    OutputConfig,
    ProcessingConfig,
)


class TestProcessingConfig:
    """Test ProcessingConfig dataclass functionality."""

    def test_processing_config_creation_with_defaults(self):
        config = ProcessingConfig()

        assert config.max_workers == 4
        assert config.retry_attempts == 3
        assert config.enable_validation is True
        assert config.enable_balance_checking is True
        assert config.duplicate_prefix == "DUPLICATED"

    def test_processing_config_creation_with_custom_values(self):
        config = ProcessingConfig(
            max_workers=8,
            retry_attempts=5,
            enable_validation=False,
            enable_balance_checking=False,
        )

        assert config.max_workers == 8
        assert config.retry_attempts == 5
        assert config.enable_validation is False
        assert config.enable_balance_checking is False


class TestOutputConfig:
    """Test OutputConfig dataclass functionality."""

    def test_output_config_creation_with_defaults(self):
        config = OutputConfig()

        assert config.default_format == "excel"
        assert config.date_format == "%Y-%m-%d"
        assert config.decimal_separator == ","

    def test_output_config_creation_with_custom_values(self):
        config = OutputConfig(
            default_format="csv",
            date_format="%d/%m/%Y",
            decimal_separator=".",
        )

        assert config.default_format == "csv"
        assert config.date_format == "%d/%m/%Y"
        assert config.decimal_separator == "."


class TestApplicationConfig:
    """Test ApplicationConfig main configuration class."""

    def test_application_config_creation_with_required_fields(self):
        processing_config = ProcessingConfig()
        output_config = OutputConfig()

        config = ApplicationConfig(
            input_directory=Path("input"),
            output_directory=Path("output"),
            processing=processing_config,
            output=output_config,
        )

        assert config.input_directory == Path("input")
        assert config.output_directory == Path("output")
        assert config.processing == processing_config
        assert config.output == output_config
        assert config.log_level == "INFO"


class TestApplicationConfigFromYaml:
    """Test ApplicationConfig.from_yaml() method."""

    def test_from_yaml_minimal_config(self):
        yaml_content = """
input_directory: "input"
output_directory: "output"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = ApplicationConfig.from_yaml(Path("test.yaml"))

            assert config.input_directory == Path("input")
            assert config.output_directory == Path("output")
            assert config.processing.max_workers == 4
            assert config.output.default_format == "excel"
            assert config.log_level == "INFO"

    def test_from_yaml_full_config(self):
        yaml_content = """
input_directory: "input"
output_directory: "output"
log_level: "DEBUG"

processing:
  max_workers: 2
  retry_attempts: 2
  enable_validation: true
  enable_balance_checking: false

output:
  default_format: "csv"
  date_format: "%d/%m/%Y"
  decimal_separator: "."
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = ApplicationConfig.from_yaml(Path("test.yaml"))

            assert config.log_level == "DEBUG"
            assert config.processing.max_workers == 2
            assert config.processing.retry_attempts == 2
            assert config.processing.enable_balance_checking is False
            assert config.output.default_format == "csv"
            assert config.output.date_format == "%d/%m/%Y"
            assert config.output.decimal_separator == "."

    def test_from_yaml_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                ApplicationConfig.from_yaml(Path("nonexistent.yaml"))

    def test_from_yaml_invalid_yaml(self):
        invalid_yaml = """
input_directory: "input"
output_directory: "output"
malformed: [
"""
        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(yaml.YAMLError):
                ApplicationConfig.from_yaml(Path("invalid.yaml"))

    def test_from_yaml_missing_required_fields(self):
        yaml_content = """
log_level: "DEBUG"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with pytest.raises(KeyError):
                ApplicationConfig.from_yaml(Path("incomplete.yaml"))


class TestApplicationConfigFromEnvironment:
    """Test ApplicationConfig.from_environment() method."""

    def test_from_environment_all_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.input_directory == Path("input")
            assert config.output_directory == Path("output")
            assert config.log_level == "INFO"
            assert config.processing.max_workers == 4
            assert config.output.default_format == "excel"

    def test_from_environment_custom_values(self):
        env_vars = {
            "FSP_INPUT_DIR": "/custom/input",
            "FSP_OUTPUT_DIR": "/custom/output",
            "FSP_LOG_LEVEL": "DEBUG",
            "FSP_MAX_WORKERS": "8",
            "FSP_RETRY_ATTEMPTS": "5",
            "FSP_ENABLE_VALIDATION": "false",
            "FSP_OUTPUT_FORMAT": "csv",
            "FSP_DATE_FORMAT": "%d/%m/%Y",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.input_directory == Path("/custom/input")
            assert config.output_directory == Path("/custom/output")
            assert config.log_level == "DEBUG"
            assert config.processing.max_workers == 8
            assert config.processing.retry_attempts == 5
            assert config.processing.enable_validation is False
            assert config.output.default_format == "csv"
            assert config.output.date_format == "%d/%m/%Y"

    def test_from_environment_boolean_parsing(self):
        env_vars = {
            "FSP_ENABLE_VALIDATION": "False",
            "FSP_ENABLE_BALANCE_CHECK": "1",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.processing.enable_validation is False
            assert config.processing.enable_balance_checking is False
