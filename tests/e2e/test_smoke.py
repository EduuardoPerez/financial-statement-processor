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

import pytest


class TestCLISmoke:
    """End-to-end smoke test for CLI process command."""

    def setup_method(self):
        """Setup test environment."""
        self.test_data_dir = Path("tests/test_data/input")
        self.temp_output_dir = Path(tempfile.mkdtemp(prefix="fsp_e2e_"))
        self.output_files = []

    def teardown_method(self):
        """Clean up generated files."""
        for output_file in self.output_files:
            if output_file.exists():
                output_file.unlink()

        if self.temp_output_dir.exists():
            try:
                self.temp_output_dir.rmdir()
            except OSError:
                for file in self.temp_output_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                self.temp_output_dir.rmdir()

    @pytest.mark.parametrize(
        "input_filename, output_filename",
        [
            (
                "MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf",
                "MACRO_VISA_20220525.xlsx",
            ),
            (
                "BBVA-VISA-resumen_cuenta_visa_May_2025.pdf",
                "BBVA_VISA_20250430.xlsx",
            ),
        ],
    )
    def test_cli_process_pdf(self, input_filename, output_filename):
        """Test CLI process command end-to-end for supported PDF formats."""
        input_file = self.test_data_dir / input_filename
        assert input_file.exists(), f"Test input file not found: {input_file}"

        expected_output = self.temp_output_dir / output_filename
        self.output_files.append(expected_output)

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

        env = os.environ.copy()
        env["PYTHONPATH"] = "src"

        result = subprocess.run(
            cmd, cwd=Path.cwd(), env=env, capture_output=True, text=True
        )

        assert result.returncode == 0, (
            f"CLI process command failed with exit code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        assert expected_output.exists(), (
            f"Output file was not created: {expected_output}\n"
            f"CLI output: {result.stdout}"
        )

        assert expected_output.stat().st_size > 0, "Output file is empty"

    def test_cli_process_failure_case(self):
        """Test CLI process command with invalid input to ensure proper error handling."""
        input_file = self.test_data_dir / "nonexistent-file.pdf"

        cmd = ["uv", "run", "python", "-m", "cli.main", "process", str(input_file)]

        env = os.environ.copy()
        env["PYTHONPATH"] = "src"

        result = subprocess.run(
            cmd, cwd=Path.cwd(), env=env, capture_output=True, text=True
        )

        assert result.returncode != 0, (
            f"CLI should have failed for non-existent file but returned {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
