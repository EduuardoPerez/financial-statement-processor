"""
End-to-end smoke test for the CLI process command.

This test validates that the complete CLI pipeline works by:
1. Running the CLI process command via subprocess
2. Asserting successful exit code (0)
3. Asserting that output file is created
4. Cleaning up generated files

Usage:
    uv run --module pytest -q tests/e2e/test_smoke.py
"""

import os
import subprocess
import tempfile
from pathlib import Path


class TestCLISmoke:
    """End-to-end smoke test for CLI process command."""

    def setup_method(self):
        """Setup test environment."""
        self.test_data_dir = Path("tests/test_data/input")
        self.temp_output_dir = Path(tempfile.mkdtemp(prefix="fsp_e2e_"))
        self.output_files = []

    def teardown_method(self):
        """Clean up generated files."""
        # Remove any generated output files
        for output_file in self.output_files:
            if output_file.exists():
                output_file.unlink()

        # Remove temporary output directory
        if self.temp_output_dir.exists():
            try:
                self.temp_output_dir.rmdir()
            except OSError:
                # Directory not empty, remove remaining files
                for file in self.temp_output_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                self.temp_output_dir.rmdir()

    def test_cli_process_macro_visa_pdf(self):
        """Test CLI process command with MACRO VISA PDF."""
        # Use well-tested sample file
        input_file = self.test_data_dir / "MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"

        # Ensure input file exists
        assert input_file.exists(), f"Test input file not found: {input_file}"

        # Expected output file (based on CLI implementation)
        expected_output = self.temp_output_dir / "MACRO_VISA_20220525.xlsx"
        self.output_files.append(expected_output)

        # Build CLI command
        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "cli.main",
            "process",
            str(input_file),
            "--output",
            str(expected_output),
        ]

        # Set environment with PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"

        # Execute CLI command
        result = subprocess.run(
            cmd, cwd=Path.cwd(), env=env, capture_output=True, text=True
        )

        # Assert successful execution
        assert result.returncode == 0, (
            f"CLI process command failed with exit code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Assert output file was created
        assert expected_output.exists(), (
            f"Output file was not created: {expected_output}\n"
            f"CLI output: {result.stdout}"
        )

        # Optional: Basic validation that file has content
        assert expected_output.stat().st_size > 0, "Output file is empty"

    def test_cli_process_bbva_visa_pdf(self):
        """Test CLI process command with BBVA VISA PDF."""
        # Use another well-tested sample file
        input_file = self.test_data_dir / "BBVA-VISA-resumen_cuenta_visa_May_2025.pdf"

        # Ensure input file exists
        assert input_file.exists(), f"Test input file not found: {input_file}"

        # Expected output file (based on CLI implementation)
        expected_output = self.temp_output_dir / "BBVA_VISA_20250430.xlsx"
        self.output_files.append(expected_output)

        # Build CLI command
        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "cli.main",
            "process",
            str(input_file),
            "--output",
            str(expected_output),
        ]

        # Set environment with PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"

        # Execute CLI command
        result = subprocess.run(
            cmd, cwd=Path.cwd(), env=env, capture_output=True, text=True
        )

        # Assert successful execution
        assert result.returncode == 0, (
            f"CLI process command failed with exit code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Assert output file was created
        assert expected_output.exists(), (
            f"Output file was not created: {expected_output}\n"
            f"CLI output: {result.stdout}"
        )

        # Optional: Basic validation that file has content
        assert expected_output.stat().st_size > 0, "Output file is empty"

    def test_cli_process_failure_case(self):
        """Test CLI process command with invalid input to ensure proper error handling."""
        # Use non-existent file
        input_file = self.test_data_dir / "nonexistent-file.pdf"

        # Build CLI command
        cmd = ["uv", "run", "python", "-m", "cli.main", "process", str(input_file)]

        # Set environment with PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"

        # Execute CLI command
        result = subprocess.run(
            cmd, cwd=Path.cwd(), env=env, capture_output=True, text=True
        )

        # Assert failure (non-zero exit code)
        assert result.returncode != 0, (
            f"CLI should have failed for non-existent file but returned {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
