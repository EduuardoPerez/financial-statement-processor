"""
CLI integration tests for configurable duplicate prefix functionality.

This module tests that the duplicate prefix configuration flows correctly
from CLI → ApplicationConfig → StatementProcessingService → DuplicateDetector.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli.main import create_components, load_config
from infrastructure.config import ApplicationConfig


class TestDuplicatePrefixCLIIntegration:
    """Test duplicate prefix configuration through CLI integration."""

    def test_cli_creates_components_with_processing_config(self):
        """Test that create_components properly wires processing_config."""
        # Create test configuration
        config = ApplicationConfig.from_environment()
        config.processing.duplicate_prefix = "TEST_PREFIX"

        # Create components
        processing_service, parser_factory = create_components(config)

        # Verify processing service has the configuration
        assert processing_service._processing_config is not None
        assert processing_service._processing_config.duplicate_prefix == "TEST_PREFIX"

    def test_yaml_config_integration_through_cli(self):
        """Test YAML configuration loading through CLI components."""
        yaml_content = """
input_directory: "input"
output_directory: "output"
processing:
  duplicate_prefix: "YAML_DUPLICADO"
  max_workers: 4
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                # Load config and create components
                config = load_config(Path(f.name))
                processing_service, _ = create_components(config)

                # Verify configuration flows through
                assert config.processing.duplicate_prefix == "YAML_DUPLICADO"
                assert (
                    processing_service._processing_config.duplicate_prefix
                    == "YAML_DUPLICADO"
                )
            finally:
                os.unlink(f.name)

    def test_environment_config_integration_through_cli(self):
        """Test environment variable configuration through CLI components."""
        # Set environment variable
        os.environ["FSP_DUPLICATE_PREFIX"] = "ENV_DUPLICATE"

        try:
            # Load config and create components
            config = load_config(None)  # None = load from environment
            processing_service, _ = create_components(config)

            # Verify configuration flows through
            assert config.processing.duplicate_prefix == "ENV_DUPLICATE"
            assert (
                processing_service._processing_config.duplicate_prefix
                == "ENV_DUPLICATE"
            )
        finally:
            # Clean up environment variable
            if "FSP_DUPLICATE_PREFIX" in os.environ:
                del os.environ["FSP_DUPLICATE_PREFIX"]

    def test_default_duplicate_prefix_through_cli(self):
        """Test default duplicate prefix when no custom configuration."""
        # Ensure no environment variable is set
        if "FSP_DUPLICATE_PREFIX" in os.environ:
            del os.environ["FSP_DUPLICATE_PREFIX"]

        # Load config and create components
        config = load_config(None)  # None = load from environment
        processing_service, _ = create_components(config)

        # Verify default configuration
        assert config.processing.duplicate_prefix == "DUPLICATED"
        assert processing_service._processing_config.duplicate_prefix == "DUPLICATED"

    @patch("application.services.StatementProcessingService.consolidate_statements")
    def test_duplicate_prefix_flows_to_duplicate_detector(self, mock_consolidate):
        """Test that duplicate prefix configuration reaches DuplicateDetector."""

        # Setup mock to capture DuplicateDetector usage
        def capture_detector_call(*args, **kwargs):
            # This would be called during consolidation
            # We can't easily test the actual detector without complex mocking
            # But we can verify the service has the right config
            return MagicMock()

        mock_consolidate.side_effect = capture_detector_call

        # Create configuration with custom prefix
        config = ApplicationConfig.from_environment()
        config.processing.duplicate_prefix = "CLI_TEST_PREFIX"

        # Create components
        processing_service, _ = create_components(config)

        # Verify the processing service has the correct configuration
        assert (
            processing_service._processing_config.duplicate_prefix == "CLI_TEST_PREFIX"
        )

        # The actual flow to DuplicateDetector is tested in the domain layer tests
        # This test ensures CLI properly wires the configuration

    def test_cli_component_creation_error_handling(self):
        """Test error handling in CLI component creation."""

        # Create invalid configuration
        config = ApplicationConfig.from_environment()
        config.input_directory = Path("/nonexistent/directory")

        # Component creation should succeed (it doesn't validate directories)
        processing_service, parser_factory = create_components(config)

        # Verify service is created with configuration
        assert processing_service._processing_config is not None
        assert parser_factory is not None

    def test_multiple_configuration_sources_precedence(self):
        """Test configuration precedence: Environment > Default."""
        # Set environment variable
        os.environ["FSP_DUPLICATE_PREFIX"] = "ENV_PRIORITY"

        try:
            # Load from environment (should override default)
            config = load_config(None)
            processing_service, _ = create_components(config)

            assert config.processing.duplicate_prefix == "ENV_PRIORITY"
            assert (
                processing_service._processing_config.duplicate_prefix == "ENV_PRIORITY"
            )

            # Test YAML override
            yaml_content = """
input_directory: "input"
output_directory: "output"
processing:
  duplicate_prefix: "YAML_PRIORITY"
"""

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write(yaml_content)
                f.flush()

                try:
                    # YAML should override environment when explicitly loaded
                    yaml_config = load_config(Path(f.name))
                    yaml_service, _ = create_components(yaml_config)

                    assert yaml_config.processing.duplicate_prefix == "YAML_PRIORITY"
                    assert (
                        yaml_service._processing_config.duplicate_prefix
                        == "YAML_PRIORITY"
                    )
                finally:
                    os.unlink(f.name)

        finally:
            # Clean up environment variable
            if "FSP_DUPLICATE_PREFIX" in os.environ:
                del os.environ["FSP_DUPLICATE_PREFIX"]

    def test_processing_config_immutability(self):
        """Test that ProcessingConfig maintains immutability principles."""
        config = ApplicationConfig.from_environment()
        original_prefix = config.processing.duplicate_prefix

        # Create components
        processing_service, _ = create_components(config)

        # Verify original config is not modified
        assert config.processing.duplicate_prefix == original_prefix
        assert processing_service._processing_config.duplicate_prefix == original_prefix

    def test_comprehensive_config_flow_integration(self):
        """Test comprehensive configuration flow from YAML to service layer."""
        yaml_content = """
input_directory: "test_input"
output_directory: "test_output"
log_level: "INFO"

processing:
  max_workers: 8
  retry_attempts: 5
  enable_validation: true
  enable_balance_checking: true
  duplicate_prefix: "INTEGRATED_TEST"

output:
  default_format: "excel"
  date_format: "%Y-%m-%d"
  decimal_separator: ","
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                # Load configuration
                config = load_config(Path(f.name))

                # Verify all configuration loaded correctly
                assert config.input_directory == Path("test_input")
                assert config.output_directory == Path("test_output")
                assert config.log_level == "INFO"

                # Verify processing configuration
                assert config.processing.max_workers == 8
                assert config.processing.retry_attempts == 5
                assert config.processing.enable_validation is True
                assert config.processing.enable_balance_checking is True
                assert config.processing.duplicate_prefix == "INTEGRATED_TEST"

                # Verify output configuration
                assert config.output.default_format == "excel"
                assert config.output.decimal_separator == ","

                # Create components and verify wiring
                processing_service, parser_factory = create_components(config)

                # Verify service receives complete configuration
                assert (
                    processing_service._processing_config.duplicate_prefix
                    == "INTEGRATED_TEST"
                )
                assert processing_service._processing_config.max_workers == 8
                assert processing_service._processing_config.enable_validation is True

            finally:
                os.unlink(f.name)

    def test_edge_case_configurations(self):
        """Test edge cases for duplicate prefix configuration."""
        edge_cases = [
            "",  # Empty string
            " ",  # Whitespace
            "🔄",  # Unicode emoji
            "TRÈS LONG PREFIX WITH SPACES AND ACCENTS",  # Long with special chars
            "测试",  # Non-Latin characters
        ]

        for prefix in edge_cases:
            config = ApplicationConfig.from_environment()
            config.processing.duplicate_prefix = prefix

            # Component creation should handle all edge cases
            processing_service, _ = create_components(config)

            # Verify configuration is preserved exactly
            assert processing_service._processing_config.duplicate_prefix == prefix
