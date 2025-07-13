"""
Unit tests for CLI main module.

Tests all CLI commands and functionality including:
- Configuration loading and error handling
- Component creation and wiring
- All CLI commands (info, process, validate, batch)
- JSON and Rich console output
- Error handling and verbose modes
"""

import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest
from click.testing import CliRunner

from application.services import ProcessingResult
from cli.main import (
    CLIError,
    SimpleFileReader,
    SimpleFileWriter,
    cli,
    create_components,
    load_config,
    output_error,
    output_json,
)
from domain.models import Balance, PaymentMethod, Statement
from domain.validation import ValidationResult
from infrastructure.config import ApplicationConfig, OutputConfig, ProcessingConfig


class TestSimpleFileReader:
    """Test SimpleFileReader implementation."""

    def test_read_existing_file(self, tmp_path):
        """Test reading an existing file."""
        reader = SimpleFileReader()
        test_file = tmp_path / "test.txt"
        test_content = b"test content"
        test_file.write_bytes(test_content)

        result = reader.read(test_file)
        assert result == test_content

    def test_exists_true(self, tmp_path):
        """Test exists returns True for existing file."""
        reader = SimpleFileReader()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        assert reader.exists(test_file) is True

    def test_exists_false(self, tmp_path):
        """Test exists returns False for non-existing file."""
        reader = SimpleFileReader()
        test_file = tmp_path / "nonexistent.txt"

        assert reader.exists(test_file) is False


class TestSimpleFileWriter:
    """Test SimpleFileWriter implementation."""

    def test_write_file(self, tmp_path):
        """Test writing content to file."""
        writer = SimpleFileWriter()
        test_file = tmp_path / "test.txt"
        test_content = b"test content"

        writer.write(test_file, test_content)

        assert test_file.read_bytes() == test_content

    def test_ensure_directory_creates_directory(self, tmp_path):
        """Test ensure_directory creates directories."""
        writer = SimpleFileWriter()
        test_dir = tmp_path / "subdir" / "nested"

        writer.ensure_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directory_existing_directory(self, tmp_path):
        """Test ensure_directory with existing directory."""
        writer = SimpleFileWriter()
        test_dir = tmp_path / "existing"
        test_dir.mkdir()

        # Should not raise error
        writer.ensure_directory(test_dir)

        assert test_dir.exists()


class TestLoadConfig:
    """Test configuration loading functionality."""

    def test_load_config_from_yaml(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_content = """
input_directory: "test_input"
output_directory: "test_output"
log_level: "DEBUG"
"""
        config_file.write_text(config_content)

        with patch(
            "infrastructure.config.ApplicationConfig.from_yaml"
        ) as mock_from_yaml:
            mock_config = Mock(spec=ApplicationConfig)
            mock_from_yaml.return_value = mock_config

            result = load_config(config_file)

            mock_from_yaml.assert_called_once_with(config_file)
            assert result == mock_config

    def test_load_config_from_environment(self):
        """Test loading configuration from environment."""
        with patch(
            "infrastructure.config.ApplicationConfig.from_environment"
        ) as mock_from_env:
            mock_config = Mock(spec=ApplicationConfig)
            mock_from_env.return_value = mock_config

            result = load_config(None)

            mock_from_env.assert_called_once()
            assert result == mock_config

    def test_load_config_yaml_error(self, tmp_path):
        """Test load_config raises CLIError when YAML loading fails."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:")

        with patch(
            "infrastructure.config.ApplicationConfig.from_yaml",
            side_effect=Exception("YAML error"),
        ):
            with pytest.raises(
                CLIError, match="Failed to load configuration: YAML error"
            ):
                load_config(config_file)

    def test_load_config_environment_error(self):
        """Test load_config raises CLIError when environment loading fails."""
        with patch(
            "infrastructure.config.ApplicationConfig.from_environment",
            side_effect=Exception("Env error"),
        ):
            with pytest.raises(
                CLIError, match="Failed to load configuration: Env error"
            ):
                load_config(None)


class TestCreateComponents:
    """Test component creation and wiring."""

    @patch("cli.main.StatementProcessingService")
    @patch("cli.main.ExcelStatementRepository")
    @patch("cli.main.FilenameGenerator")
    @patch("cli.main.StatementValidator")
    @patch("cli.main.DefaultParserFactory")
    @patch("cli.main.PaymentMethodDetector")
    def test_create_components_success(
        self,
        mock_detector_class,
        mock_factory_class,
        mock_validator_class,
        mock_filename_gen_class,
        mock_repository_class,
        mock_service_class,
    ):
        """Test successful component creation."""
        # Setup mocks
        mock_config = Mock(spec=ApplicationConfig)
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        mock_filename_gen = Mock()
        mock_filename_gen_class.return_value = mock_filename_gen
        mock_repository = Mock()
        mock_repository_class.return_value = mock_repository
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Execute
        result_service, result_factory = create_components(mock_config)

        # Verify
        assert result_service == mock_service
        assert result_factory == mock_factory

        # Verify detector registration calls
        assert mock_detector.register_detector.call_count == 2

        # Verify service creation with proper dependencies
        # Extract the actual call to check parameters
        actual_call = mock_service_class.call_args
        assert actual_call is not None

        # Check required parameters are present
        kwargs = actual_call.kwargs
        assert kwargs["parser_factory"] == mock_factory
        assert kwargs["repository"] == mock_repository
        assert kwargs["validator"] == mock_validator
        assert kwargs["filename_generator"] == mock_filename_gen
        # balance_extraction_service is also passed but we don't need to verify its exact value
        assert "balance_extraction_service" in kwargs

    @patch("cli.main.PaymentMethodDetector", side_effect=Exception("Component error"))
    def test_create_components_failure(self, mock_detector):
        """Test component creation failure raises CLIError."""
        mock_config = Mock(spec=ApplicationConfig)

        with pytest.raises(
            CLIError, match="Failed to initialize components: Component error"
        ):
            create_components(mock_config)


class TestOutputFunctions:
    """Test output utility functions."""

    def test_output_json(self, capsys):
        """Test JSON output function."""
        test_data = {"key": "value", "number": 42}

        output_json(test_data)

        captured = capsys.readouterr()
        parsed_output = json.loads(captured.out)
        assert parsed_output == test_data

    @patch("cli.main.console")
    def test_output_error_simple(self, mock_console):
        """Test simple error output."""
        output_error("Test error message")

        mock_console.print.assert_called_once_with(
            "[red]❌ Error: Test error message[/red]"
        )

    @patch("cli.main.console")
    @patch("cli.main.traceback.format_exc", return_value="Traceback details")
    def test_output_error_verbose(self, mock_format_exc, mock_console):
        """Test verbose error output with exception."""
        exception = Exception("Test exception")

        output_error("Test error", verbose=True, exception=exception)

        expected_calls = [
            call("[red]❌ Error: Test error[/red]"),
            call("\n[yellow]Full Error Details:[/yellow]"),
            call("Traceback details"),
        ]
        mock_console.print.assert_has_calls(expected_calls)


class TestCLIGroup:
    """Test main CLI group and context setup."""

    @patch("cli.main.create_components")
    def test_cli_group_with_config(self, mock_create_components, tmp_path):
        """Test CLI group with config file option."""
        runner = CliRunner()
        config_file = tmp_path / "config.yaml"
        config_file.write_text("input_directory: test")

        with patch("cli.main.load_config") as mock_load_config:
            mock_config = Mock(spec=ApplicationConfig)
            mock_config.log_level = "INFO"
            mock_config.input_directory = Path("test_input")
            mock_config.output_directory = Path("test_output")
            mock_config.enable_async = False
            mock_config.processing = Mock(spec=ProcessingConfig)
            mock_config.processing.max_workers = 4
            mock_config.processing.enable_validation = True
            mock_config.processing.enable_balance_checking = True
            mock_config.output = Mock(spec=OutputConfig)
            mock_config.output.default_format = "excel"
            mock_load_config.return_value = mock_config

            # Mock create_components for info command
            mock_factory = Mock()
            mock_factory.get_supported_extensions.return_value = {
                ".pdf",
                ".xls",
                ".xlsx",
            }
            mock_create_components.return_value = (Mock(), mock_factory)

            result = runner.invoke(cli, ["--config", str(config_file), "info"])

            assert result.exit_code == 0
            mock_load_config.assert_called_once_with(config_file)

    def test_cli_group_verbose_mode(self):
        """Test CLI group with verbose flag."""
        runner = CliRunner()

        with patch("cli.main.load_config") as mock_load_config:
            mock_config = Mock(spec=ApplicationConfig)
            mock_config.log_level = "INFO"
            mock_load_config.return_value = mock_config

            runner.invoke(cli, ["--verbose", "info"])

            # Verify log level was set to DEBUG for verbose mode
            assert mock_config.log_level == "DEBUG"

    def test_cli_group_config_error(self):
        """Test CLI group handles configuration errors."""
        runner = CliRunner()

        with patch("cli.main.load_config", side_effect=CLIError("Config error")):
            result = runner.invoke(cli, ["info"])

            assert result.exit_code == 1
            assert "Config error" in result.output

    def test_cli_group_unexpected_error(self):
        """Test CLI group handles unexpected errors."""
        runner = CliRunner()

        with patch(
            "cli.main.load_config", side_effect=RuntimeError("Unexpected error")
        ):
            result = runner.invoke(cli, ["info"])

            assert result.exit_code == 1
            assert "Unexpected error" in result.output


class TestInfoCommand:
    """Test info command functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.runner = CliRunner()
        self.mock_config = Mock(spec=ApplicationConfig)
        self.mock_config.input_directory = Path("test_input")
        self.mock_config.output_directory = Path("test_output")
        self.mock_config.log_level = "INFO"
        self.mock_config.enable_async = False
        self.mock_config.processing = Mock(spec=ProcessingConfig)
        self.mock_config.processing.max_workers = 4
        self.mock_config.processing.enable_validation = True
        self.mock_config.processing.enable_balance_checking = True
        self.mock_config.output = Mock(spec=OutputConfig)
        self.mock_config.output.default_format = "excel"

    @patch("cli.main.create_components")
    def test_info_command_success(self, mock_create_components):
        """Test successful info command execution."""
        mock_factory = Mock()
        mock_factory.get_supported_extensions.return_value = {".pdf", ".xls", ".xlsx"}
        mock_create_components.return_value = (Mock(), mock_factory)

        result = self.runner.invoke(
            cli, ["info"], obj={"config": self.mock_config, "verbose": False}
        )

        # Should complete successfully
        assert result.exit_code == 0

    @patch("cli.main.create_components")
    def test_info_command_json_output(self, mock_create_components):
        """Test info command with JSON output."""
        mock_factory = Mock()
        mock_factory.get_supported_extensions.return_value = {".pdf", ".xls"}
        mock_create_components.return_value = (Mock(), mock_factory)

        result = self.runner.invoke(
            cli, ["info", "--json"], obj={"config": self.mock_config, "verbose": False}
        )

        assert result.exit_code == 0
        # Verify JSON output is valid
        output_data = json.loads(result.output)
        assert "version" in output_data
        assert "config" in output_data
        assert "supported_banks" in output_data
        assert "supported_extensions" in output_data

    @patch(
        "cli.main.create_components", side_effect=Exception("Component creation failed")
    )
    def test_info_command_failure(self, mock_create_components):
        """Test info command handles component creation failures."""
        result = self.runner.invoke(
            cli, ["info"], obj={"config": self.mock_config, "verbose": False}
        )

        assert result.exit_code == 1
        assert "Failed to display info" in result.output


class TestProcessCommand:
    """Test process command functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.runner = CliRunner()
        self.mock_config = Mock(spec=ApplicationConfig)
        self.mock_config.output_directory = Path("output")

    def create_mock_processing_result(self, success=True, transaction_count=10):
        """Create a mock ProcessingResult."""
        mock_statement = Mock(spec=Statement)
        mock_statement.transactions = [Mock()] * transaction_count

        mock_result = Mock(spec=ProcessingResult)
        mock_result.success = success
        mock_result.input_path = Path("test.pdf")
        mock_result.output_path = Path("output/test.xlsx")
        mock_result.statement = mock_statement if success else None
        mock_result.processing_time = 1.5
        mock_result.errors = [] if success else ["Processing error"]

        return mock_result

    @patch("cli.main.create_components")
    def test_process_command_success(self, mock_create_components, tmp_path):
        """Test successful process command execution."""
        # Setup
        input_file = tmp_path / "test.pdf"
        input_file.write_text("test content")

        mock_service = Mock()
        mock_result = self.create_mock_processing_result(success=True)
        mock_service.process_statement.return_value = mock_result
        mock_create_components.return_value = (mock_service, Mock())

        # Execute
        result = self.runner.invoke(
            cli,
            ["process", str(input_file)],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        assert "Successfully processed" in result.output
        mock_service.process_statement.assert_called_once()

    @patch("cli.main.create_components")
    def test_process_command_json_output(self, mock_create_components, tmp_path):
        """Test process command with JSON output."""
        # Setup
        input_file = tmp_path / "test.pdf"
        input_file.write_text("test content")

        mock_service = Mock()
        mock_result = self.create_mock_processing_result(success=True)
        mock_service.process_statement.return_value = mock_result
        mock_create_components.return_value = (mock_service, Mock())

        # Execute
        result = self.runner.invoke(
            cli,
            ["process", str(input_file), "--json"],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["success"] is True
        assert output_data["transaction_count"] == 10

    @patch("cli.main.create_components")
    def test_process_command_failure(self, mock_create_components, tmp_path):
        """Test process command handles processing failures."""
        # Setup
        input_file = tmp_path / "test.pdf"
        input_file.write_text("test content")

        mock_service = Mock()
        mock_result = self.create_mock_processing_result(success=False)
        mock_service.process_statement.return_value = mock_result
        mock_create_components.return_value = (mock_service, Mock())

        # Execute
        result = self.runner.invoke(
            cli,
            ["process", str(input_file)],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 1
        assert "Failed to process" in result.output

    @patch("cli.main.create_components")
    def test_process_command_with_output_path(self, mock_create_components, tmp_path):
        """Test process command with custom output path."""
        # Setup
        input_file = tmp_path / "test.pdf"
        input_file.write_text("test content")
        output_file = tmp_path / "custom.xlsx"

        mock_service = Mock()
        mock_result = self.create_mock_processing_result(success=True)
        mock_service.process_statement.return_value = mock_result
        mock_create_components.return_value = (mock_service, Mock())

        # Execute
        result = self.runner.invoke(
            cli,
            ["process", str(input_file), "--output", str(output_file)],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        # Verify service was called with output parent directory
        mock_service.process_statement.assert_called_once_with(
            input_file, output_file.parent
        )


class TestValidateCommand:
    """Test validate command functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.runner = CliRunner()
        self.mock_config = Mock(spec=ApplicationConfig)

    def create_mock_validation_result(self, is_valid=True):
        """Create a mock validation result."""
        mock_validation = Mock(spec=ValidationResult)
        mock_validation.is_valid = is_valid
        mock_validation.errors = [] if is_valid else ["Validation error"]

        # Create mock statement
        mock_statement = Mock(spec=Statement)
        mock_statement.transactions = [Mock()] * 5
        mock_statement.payment_method = PaymentMethod.BBVA_VISA
        mock_balance = Mock(spec=Balance)
        mock_balance.ars_amount = Decimal("1000.00")
        mock_balance.usd_amount = Decimal("100.00")
        mock_statement.get_balance.return_value = mock_balance

        # Create mock result
        mock_result = Mock(spec=ProcessingResult)
        mock_result.success = is_valid
        mock_result.validation_result = mock_validation
        mock_result.statement = mock_statement if is_valid else None
        mock_result.processing_time = 0.8
        mock_result.errors = [] if is_valid else ["Processing error"]

        return mock_result

    @patch("cli.main.create_components")
    @patch("cli.main.Path.mkdir")
    @patch("cli.main.Path.rmdir")
    def test_validate_command_success(
        self, mock_rmdir, mock_mkdir, mock_create_components, tmp_path
    ):
        """Test successful validate command execution."""
        # Setup
        input_file = tmp_path / "test.pdf"
        input_file.write_text("test content")

        mock_service = Mock()
        mock_result = self.create_mock_validation_result(is_valid=True)
        mock_result.output_path = Mock()
        mock_result.output_path.exists.return_value = True
        mock_service.process_statement.return_value = mock_result
        mock_create_components.return_value = (mock_service, Mock())

        # Execute
        result = self.runner.invoke(
            cli,
            ["validate", str(input_file)],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        assert "VALID" in result.output

    @patch("cli.main.create_components")
    def test_validate_command_quick_mode(self, mock_create_components, tmp_path):
        """Test validate command in quick mode."""
        # Setup
        input_file = tmp_path / "test.pdf"
        input_file.write_text("test content")

        mock_service = Mock()
        mock_result = self.create_mock_validation_result(is_valid=True)
        mock_result.output_path = Mock()
        mock_result.output_path.exists.return_value = False
        mock_service.process_statement.return_value = mock_result
        mock_create_components.return_value = (mock_service, Mock())

        # Execute
        result = self.runner.invoke(
            cli,
            ["validate", str(input_file), "--quick"],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        assert "✅ VALID" in result.output

    @patch("cli.main.create_components")
    def test_validate_command_json_output(self, mock_create_components, tmp_path):
        """Test validate command with JSON output."""
        # Setup
        input_file = tmp_path / "test.pdf"
        input_file.write_text("test content")

        mock_service = Mock()
        mock_result = self.create_mock_validation_result(is_valid=True)
        mock_result.output_path = Mock()
        mock_result.output_path.exists.return_value = False
        mock_service.process_statement.return_value = mock_result
        mock_create_components.return_value = (mock_service, Mock())

        # Execute
        result = self.runner.invoke(
            cli,
            ["validate", str(input_file), "--json"],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["valid"] is True
        assert output_data["transaction_count"] == 5

    @patch("cli.main.create_components")
    def test_validate_command_failure(self, mock_create_components, tmp_path):
        """Test validate command handles validation failures."""
        # Setup
        input_file = tmp_path / "test.pdf"
        input_file.write_text("test content")

        mock_service = Mock()
        mock_result = self.create_mock_validation_result(is_valid=False)
        mock_result.output_path = Mock()
        mock_result.output_path.exists.return_value = False
        mock_service.process_statement.return_value = mock_result
        mock_create_components.return_value = (mock_service, Mock())

        # Execute
        result = self.runner.invoke(
            cli,
            ["validate", str(input_file)],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 1
        assert "INVALID" in result.output


class TestBatchCommand:
    """Test batch command functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.runner = CliRunner()
        self.mock_config = Mock(spec=ApplicationConfig)
        self.mock_config.output_directory = Path("output")

    @patch("cli.main.create_components")
    def test_batch_command_success(self, mock_create_components, tmp_path):
        """Test successful batch command execution."""
        # Setup input directory with files
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create test files
        (input_dir / "test1.pdf").write_text("content1")
        (input_dir / "test2.xls").write_text("content2")

        # Setup mocks
        mock_service = Mock()
        mock_factory = Mock()
        mock_factory.get_supported_extensions.return_value = {".pdf", ".xls", ".xlsx"}

        # Create successful results
        def mock_process_statement(file_path, output_dir):
            mock_statement = Mock()
            mock_statement.transactions = [Mock()] * 10
            mock_result = Mock(spec=ProcessingResult)
            mock_result.success = True
            mock_result.statement = mock_statement
            mock_result.output_path = output_dir / f"{file_path.stem}.xlsx"
            mock_result.processing_time = 1.0
            return mock_result

        mock_service.process_statement.side_effect = mock_process_statement
        mock_create_components.return_value = (mock_service, mock_factory)

        # Execute
        result = self.runner.invoke(
            cli,
            ["batch", str(input_dir)],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        assert "Batch Processing Complete" in result.output
        assert "2/2 files" in result.output

    @patch("cli.main.create_components")
    @patch("cli.main.Progress")
    def test_batch_command_json_output(
        self, mock_progress_class, mock_create_components, tmp_path
    ):
        """Test batch command with JSON output."""
        # Setup input directory
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.pdf").write_text("content")

        # Mock Progress to prevent console output
        mock_progress = Mock()
        mock_progress_class.return_value.__enter__.return_value = mock_progress
        mock_progress.add_task.return_value = "task_id"

        # Setup mocks
        mock_service = Mock()
        mock_factory = Mock()
        mock_factory.get_supported_extensions.return_value = {".pdf"}

        mock_statement = Mock()
        mock_statement.transactions = [Mock()] * 5
        mock_result = Mock(spec=ProcessingResult)
        mock_result.success = True
        mock_result.statement = mock_statement
        mock_result.output_path = Path("output/test.xlsx")
        mock_result.processing_time = 1.0
        mock_service.process_statement.return_value = mock_result
        mock_create_components.return_value = (mock_service, mock_factory)

        # Execute
        result = self.runner.invoke(
            cli,
            ["batch", str(input_dir), "--json"],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["total_files"] == 1
        assert output_data["successful"] == 1
        assert output_data["failed"] == 0

    @patch("cli.main.create_components")
    def test_batch_command_no_files(self, mock_create_components, tmp_path):
        """Test batch command with no supported files."""
        # Setup empty input directory
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Setup mocks
        mock_factory = Mock()
        mock_factory.get_supported_extensions.return_value = {".pdf", ".xls"}
        mock_create_components.return_value = (Mock(), mock_factory)

        # Execute
        result = self.runner.invoke(
            cli,
            ["batch", str(input_dir)],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        assert "No supported files found" in result.output

    @patch("cli.main.create_components")
    def test_batch_command_with_failures(self, mock_create_components, tmp_path):
        """Test batch command with some file processing failures."""
        # Setup input directory
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test1.pdf").write_text("content1")
        (input_dir / "test2.pdf").write_text("content2")

        # Setup mocks
        mock_service = Mock()
        mock_factory = Mock()
        mock_factory.get_supported_extensions.return_value = {".pdf"}

        # First call succeeds, second fails
        results = []
        success_result = Mock(spec=ProcessingResult)
        success_result.success = True
        success_result.statement = Mock()
        success_result.statement.transactions = [Mock()] * 5
        success_result.processing_time = 1.0
        results.append(success_result)

        failure_result = Mock(spec=ProcessingResult)
        failure_result.success = False
        failure_result.statement = None
        failure_result.errors = ["Processing failed"]
        results.append(failure_result)

        mock_service.process_statement.side_effect = results
        mock_create_components.return_value = (mock_service, mock_factory)

        # Execute
        result = self.runner.invoke(
            cli,
            ["batch", str(input_dir)],
            obj={"config": self.mock_config, "verbose": False},
        )

        # Verify
        assert result.exit_code == 1  # Should exit with error code due to failures
        assert "Failed Files:" in result.output


class TestMainFunction:
    """Test main entry point function."""

    @patch("cli.main.cli")
    def test_main_success(self, mock_cli):
        """Test main function successful execution."""
        from cli.main import main

        main()

        mock_cli.assert_called_once()

    @patch("cli.main.cli", side_effect=KeyboardInterrupt())
    @patch("cli.main.console")
    def test_main_keyboard_interrupt(self, mock_console, mock_cli):
        """Test main function handles keyboard interrupt."""
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_console.print.assert_called_with(
            "\n[yellow]Operation cancelled by user.[/yellow]"
        )

    @patch("cli.main.cli", side_effect=Exception("Unexpected error"))
    @patch("cli.main.console")
    def test_main_unexpected_error(self, mock_console, mock_cli):
        """Test main function handles unexpected errors."""
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_console.print.assert_called_with(
            "[red]Unexpected error: Unexpected error[/red]"
        )
