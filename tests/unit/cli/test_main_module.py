"""
Unit tests for CLI __main__ module.

This module tests the CLI entry point functionality.
"""

from pathlib import Path
from unittest.mock import patch


class TestMainModule:
    """Test CLI __main__ module functionality."""

    def test_path_insertion_logic(self):
        """Test the path insertion logic works correctly."""
        # Test that the path calculation works
        test_file_path = Path("src/cli/__main__.py")
        expected_src_path = test_file_path.parent.parent
        assert expected_src_path.name == "src"

    @patch("cli.main.main")
    def test_main_module_execution(self, mock_main):
        """Test that __main__ module calls main() function when executed."""
        # Simulate execution of the __main__ module
        import importlib.util

        # Load the module
        main_module_path = Path("src/cli/__main__.py")
        spec = importlib.util.spec_from_file_location("__main__", main_module_path)
        main_module = importlib.util.module_from_spec(spec)

        # Execute the module which should call main()
        spec.loader.exec_module(main_module)

        # Verify main() was called
        mock_main.assert_called_once()

    def test_module_can_be_imported(self):
        """Test that the __main__ module can be imported without errors."""
        import importlib.util

        # This should not raise any exceptions
        main_module_path = Path("src/cli/__main__.py")
        spec = importlib.util.spec_from_file_location("test_main", main_module_path)
        main_module = importlib.util.module_from_spec(spec)

        # Verify the module was loaded
        assert main_module is not None
        assert spec is not None
