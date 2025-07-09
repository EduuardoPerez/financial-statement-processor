import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from src.infrastructure.config import (
    ApplicationConfig,
    DatabaseConfig,
    OutputConfig,
    ProcessingConfig,
)


class TestDatabaseConfig:
    """Test DatabaseConfig dataclass functionality."""

    def test_database_config_creation_with_defaults(self):
        """Test creating DatabaseConfig with default pool_size."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="user",
            password="pass",
        )

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_db"
        assert config.username == "user"
        assert config.password == "pass"
        assert config.pool_size == 5  # default value

    def test_database_config_creation_with_custom_pool_size(self):
        """Test creating DatabaseConfig with custom pool_size."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="user",
            password="pass",
            pool_size=10,
        )

        assert config.pool_size == 10


class TestProcessingConfig:
    """Test ProcessingConfig dataclass functionality."""

    def test_processing_config_creation_with_defaults(self):
        """Test creating ProcessingConfig with all default values."""
        config = ProcessingConfig()

        assert config.max_workers == 4
        assert config.chunk_size == 1000
        assert config.timeout_seconds == 300
        assert config.retry_attempts == 3
        assert config.enable_validation is True
        assert config.enable_balance_checking is True

    def test_processing_config_creation_with_custom_values(self):
        """Test creating ProcessingConfig with custom values."""
        config = ProcessingConfig(
            max_workers=8,
            chunk_size=2000,
            timeout_seconds=600,
            retry_attempts=5,
            enable_validation=False,
            enable_balance_checking=False,
        )

        assert config.max_workers == 8
        assert config.chunk_size == 2000
        assert config.timeout_seconds == 600
        assert config.retry_attempts == 5
        assert config.enable_validation is False
        assert config.enable_balance_checking is False

    def test_processing_config_partial_custom_values(self):
        """Test creating ProcessingConfig with some custom values."""
        config = ProcessingConfig(max_workers=2, chunk_size=500)

        assert config.max_workers == 2
        assert config.chunk_size == 500
        assert config.timeout_seconds == 300  # default
        assert config.retry_attempts == 3  # default
        assert config.enable_validation is True  # default
        assert config.enable_balance_checking is True  # default


class TestOutputConfig:
    """Test OutputConfig dataclass functionality."""

    def test_output_config_creation_with_defaults(self):
        """Test creating OutputConfig with all default values."""
        config = OutputConfig()

        assert config.default_format == "excel"
        assert config.excel_sheet_name == "Sheet1"
        assert config.csv_delimiter == ","
        assert config.include_index is False
        assert config.date_format == "%Y-%m-%d"

    def test_output_config_creation_with_custom_values(self):
        """Test creating OutputConfig with custom values."""
        config = OutputConfig(
            default_format="csv",
            excel_sheet_name="Transactions",
            csv_delimiter=";",
            include_index=True,
            date_format="%d/%m/%Y",
        )

        assert config.default_format == "csv"
        assert config.excel_sheet_name == "Transactions"
        assert config.csv_delimiter == ";"
        assert config.include_index is True
        assert config.date_format == "%d/%m/%Y"

    def test_output_config_partial_custom_values(self):
        """Test creating OutputConfig with some custom values."""
        config = OutputConfig(default_format="json", include_index=True)

        assert config.default_format == "json"
        assert config.include_index is True
        assert config.excel_sheet_name == "Sheet1"  # default
        assert config.csv_delimiter == ","  # default
        assert config.date_format == "%Y-%m-%d"  # default


class TestApplicationConfig:
    """Test ApplicationConfig main configuration class."""

    def test_application_config_creation_with_required_fields(self):
        """Test creating ApplicationConfig with required fields."""
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
        assert config.database is None  # default
        assert config.log_level == "INFO"  # default
        assert config.enable_async is False  # default

    def test_application_config_creation_with_all_fields(self):
        """Test creating ApplicationConfig with all fields including database."""
        processing_config = ProcessingConfig(max_workers=8)
        output_config = OutputConfig(default_format="csv")
        database_config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="user",
            password="pass",
        )

        config = ApplicationConfig(
            input_directory=Path("input"),
            output_directory=Path("output"),
            processing=processing_config,
            output=output_config,
            database=database_config,
            log_level="DEBUG",
            enable_async=True,
        )

        assert config.input_directory == Path("input")
        assert config.output_directory == Path("output")
        assert config.processing == processing_config
        assert config.output == output_config
        assert config.database == database_config
        assert config.log_level == "DEBUG"
        assert config.enable_async is True


class TestApplicationConfigFromYaml:
    """Test ApplicationConfig.from_yaml() method."""

    def test_from_yaml_minimal_config(self):
        """Test loading minimal YAML configuration."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = ApplicationConfig.from_yaml(Path("test.yaml"))

            assert config.input_directory == Path("input")
            assert config.output_directory == Path("output")
            assert config.processing.max_workers == 4  # default
            assert config.output.default_format == "excel"  # default
            assert config.database is None
            assert config.log_level == "INFO"  # default
            assert config.enable_async is False  # default

    def test_from_yaml_full_config_without_database(self):
        """Test loading full YAML configuration without database."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
log_level: "DEBUG"
enable_async: true

processing:
  max_workers: 2
  chunk_size: 500
  timeout_seconds: 60
  retry_attempts: 2
  enable_validation: true
  enable_balance_checking: false

output:
  default_format: "csv"
  excel_sheet_name: "Transactions"
  csv_delimiter: ";"
  include_index: true
  date_format: "%d/%m/%Y"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = ApplicationConfig.from_yaml(Path("test.yaml"))

            assert config.input_directory == Path("input")
            assert config.output_directory == Path("output")
            assert config.log_level == "DEBUG"
            assert config.enable_async is True

            assert config.processing.max_workers == 2
            assert config.processing.chunk_size == 500
            assert config.processing.timeout_seconds == 60
            assert config.processing.retry_attempts == 2
            assert config.processing.enable_validation is True
            assert config.processing.enable_balance_checking is False

            assert config.output.default_format == "csv"
            assert config.output.excel_sheet_name == "Transactions"
            assert config.output.csv_delimiter == ";"
            assert config.output.include_index is True
            assert config.output.date_format == "%d/%m/%Y"

            assert config.database is None

    def test_from_yaml_full_config_with_database(self):
        """Test loading full YAML configuration with database."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
log_level: "INFO"
enable_async: false

processing:
  max_workers: 8
  chunk_size: 2000
  timeout_seconds: 600
  retry_attempts: 5
  enable_validation: true
  enable_balance_checking: true

output:
  default_format: "excel"
  excel_sheet_name: "Sheet1"
  include_index: false
  date_format: "%Y-%m-%d"

database:
  host: "postgres.internal"
  port: 5432
  database: "financial_statements"
  username: "fsp_user"
  password: "secret"
  pool_size: 10
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = ApplicationConfig.from_yaml(Path("test.yaml"))

            assert config.input_directory == Path("input")
            assert config.output_directory == Path("output")
            assert config.log_level == "INFO"
            assert config.enable_async is False

            assert config.processing.max_workers == 8
            assert config.processing.chunk_size == 2000
            assert config.processing.timeout_seconds == 600
            assert config.processing.retry_attempts == 5
            assert config.processing.enable_validation is True
            assert config.processing.enable_balance_checking is True

            assert config.output.default_format == "excel"
            assert config.output.excel_sheet_name == "Sheet1"
            assert config.output.include_index is False
            assert config.output.date_format == "%Y-%m-%d"

            assert config.database is not None
            assert config.database.host == "postgres.internal"
            assert config.database.port == 5432
            assert config.database.database == "financial_statements"
            assert config.database.username == "fsp_user"
            assert config.database.password == "secret"
            assert config.database.pool_size == 10

    def test_from_yaml_file_not_found(self):
        """Test handling of file not found error."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                ApplicationConfig.from_yaml(Path("nonexistent.yaml"))

    def test_from_yaml_invalid_yaml(self):
        """Test handling of invalid YAML content."""
        invalid_yaml = """
input_directory: "input"
output_directory: "output"
malformed: [
"""
        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(yaml.YAMLError):
                ApplicationConfig.from_yaml(Path("invalid.yaml"))

    def test_from_yaml_missing_required_fields(self):
        """Test handling of missing required fields."""
        yaml_content = """
log_level: "DEBUG"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with pytest.raises(KeyError):
                ApplicationConfig.from_yaml(Path("incomplete.yaml"))


class TestApplicationConfigFromEnvironment:
    """Test ApplicationConfig.from_environment() method."""

    def test_from_environment_all_defaults(self):
        """Test loading configuration from environment with all defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.input_directory == Path("input")
            assert config.output_directory == Path("output")
            assert config.log_level == "INFO"
            assert config.enable_async is False

            assert config.processing.max_workers == 4
            assert config.processing.chunk_size == 1000
            assert config.processing.timeout_seconds == 300
            assert config.processing.retry_attempts == 3
            assert config.processing.enable_validation is True
            assert config.processing.enable_balance_checking is True

            assert config.output.default_format == "excel"
            assert config.output.excel_sheet_name == "Sheet1"
            assert config.output.csv_delimiter == ","
            assert config.output.include_index is False
            assert config.output.date_format == "%Y-%m-%d"

            assert config.database is None

    def test_from_environment_custom_values(self):
        """Test loading configuration from environment with custom values."""
        env_vars = {
            "FSP_INPUT_DIR": "/custom/input",
            "FSP_OUTPUT_DIR": "/custom/output",
            "FSP_LOG_LEVEL": "DEBUG",
            "FSP_ENABLE_ASYNC": "true",
            "FSP_MAX_WORKERS": "8",
            "FSP_CHUNK_SIZE": "2000",
            "FSP_TIMEOUT": "600",
            "FSP_RETRY_ATTEMPTS": "5",
            "FSP_ENABLE_VALIDATION": "false",
            "FSP_ENABLE_BALANCE_CHECK": "false",
            "FSP_OUTPUT_FORMAT": "csv",
            "FSP_EXCEL_SHEET": "Transactions",
            "FSP_CSV_DELIMITER": ";",
            "FSP_INCLUDE_INDEX": "true",
            "FSP_DATE_FORMAT": "%d/%m/%Y",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.input_directory == Path("/custom/input")
            assert config.output_directory == Path("/custom/output")
            assert config.log_level == "DEBUG"
            assert config.enable_async is True

            assert config.processing.max_workers == 8
            assert config.processing.chunk_size == 2000
            assert config.processing.timeout_seconds == 600
            assert config.processing.retry_attempts == 5
            assert config.processing.enable_validation is False
            assert config.processing.enable_balance_checking is False

            assert config.output.default_format == "csv"
            assert config.output.excel_sheet_name == "Transactions"
            assert config.output.csv_delimiter == ";"
            assert config.output.include_index is True
            assert config.output.date_format == "%d/%m/%Y"

            assert config.database is None

    def test_from_environment_with_database(self):
        """Test loading configuration from environment with database config."""
        env_vars = {
            "FSP_INPUT_DIR": "input",
            "FSP_OUTPUT_DIR": "output",
            "FSP_DB_HOST": "localhost",
            "FSP_DB_PORT": "5432",
            "FSP_DB_NAME": "test_db",
            "FSP_DB_USER": "test_user",
            "FSP_DB_PASSWORD": "test_pass",
            "FSP_DB_POOL_SIZE": "8",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.database is not None
            assert config.database.host == "localhost"
            assert config.database.port == 5432
            assert config.database.database == "test_db"
            assert config.database.username == "test_user"
            assert config.database.password == "test_pass"
            assert config.database.pool_size == 8

    def test_from_environment_boolean_parsing(self):
        """Test boolean parsing from environment variables."""
        env_vars = {
            "FSP_ENABLE_ASYNC": "TRUE",
            "FSP_ENABLE_VALIDATION": "False",
            "FSP_ENABLE_BALANCE_CHECK": "1",
            "FSP_INCLUDE_INDEX": "0",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.enable_async is True  # "TRUE" -> True
            assert config.processing.enable_validation is False  # "False" -> False
            assert (
                config.processing.enable_balance_checking is False
            )  # "1" -> False (not "true")
            assert config.output.include_index is False  # "0" -> False

    def test_from_environment_no_database_host(self):
        """Test environment loading without database host."""
        env_vars = {
            "FSP_DB_PORT": "5432",
            "FSP_DB_NAME": "test_db",
            # No FSP_DB_HOST
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.database is None

    def test_load_database_from_env_with_defaults(self):
        """Test _load_database_from_env with default values."""
        env_vars = {
            "FSP_DB_HOST": "localhost",
            # Using defaults for other values
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment()

            assert config.database is not None
            assert config.database.host == "localhost"
            assert config.database.port == 5432  # default
            assert config.database.database == "financial_statements"  # default
            assert config.database.username == "fsp_user"  # default
            assert config.database.password == ""  # default
            assert config.database.pool_size == 5  # default

    def test_load_database_from_env_no_host(self):
        """Test _load_database_from_env returns None when no host."""
        with patch.dict(os.environ, {}, clear=True):
            database_config = ApplicationConfig._load_database_from_env()

            assert database_config is None
