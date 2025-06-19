import os

import pandas as pd
import pytest

from parse_visa_statement import (
    detect_payment_method,
    parse_mercadopago_xlsx,
    validate_mercadopago_balance,
)


class TestMercadopagoProcessing:
    """Integration tests for Mercadopago XLSX processing"""

    @pytest.fixture
    def input_file_path(self):
        return "tests/test_data/input/mercadopago.xlsx"

    @pytest.fixture
    def expected_output_path(self):
        return "tests/test_data/expected_output/mercadopago-transactions.xlsx"

    @pytest.fixture
    def test_output_path(self, tmp_path):
        return str(tmp_path / "test_mercadopago_output.xlsx")

    def test_parse_mercadopago_xlsx_integration(
        self, input_file_path, test_output_path, expected_output_path
    ):
        """Test complete Mercadopago XLSX processing workflow"""
        # Process the file
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # Verify output file was created
        assert os.path.exists(test_output_path)

        # Load expected results for comparison
        expected_df = pd.read_excel(expected_output_path)

        # Verify basic structure
        assert len(result_df) == len(expected_df)
        assert list(result_df.columns) == list(expected_df.columns)

    def test_transaction_count(self, input_file_path, test_output_path):
        """Test that all transactions are processed correctly"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # Should have 394 transactions based on expected output
        assert len(result_df) == 394

        # All transactions should have valid data
        assert result_df["Date"].notna().all()
        assert result_df["Description"].notna().all()
        assert result_df["Currency"].notna().all()
        assert result_df["Amount"].notna().all()
        assert result_df["Payment Method"].notna().all()

    def test_currency_handling(self, input_file_path, test_output_path):
        """Test that all transactions are correctly assigned ARS currency"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # All Mercadopago transactions should be in ARS
        assert (result_df["Currency"] == "ARS").all()

        # Should have no USD transactions
        usd_count = (result_df["Currency"] == "USD").sum()
        assert usd_count == 0

    def test_amount_totals(
        self, input_file_path, test_output_path, expected_output_path
    ):
        """Test that amount totals match expected values"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)
        expected_df = pd.read_excel(expected_output_path)

        # Total amounts should match
        result_total = result_df["Amount"].sum()
        expected_total = expected_df["Amount"].sum()

        assert abs(result_total - expected_total) < 0.01

        # Should match the expected total of -64,841.11
        assert abs(result_total - (-64841.11)) < 0.01

    def test_date_range_and_format(self, input_file_path, test_output_path):
        """Test date conversion and range"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # Convert dates to datetime for analysis
        result_df["Date"] = pd.to_datetime(result_df["Date"])

        # Check date range (February to June 2025)
        min_date = result_df["Date"].min()
        max_date = result_df["Date"].max()

        assert min_date.year == 2025
        assert max_date.year == 2025
        assert min_date.month == 2  # February
        assert max_date.month == 6  # June

        # Verify date format is YYYY-MM-DD when converted back to string
        date_strings = result_df["Date"].dt.strftime("%Y-%m-%d")
        assert all(len(date_str) == 10 for date_str in date_strings)
        assert all(date_str.count("-") == 2 for date_str in date_strings)

    def test_payment_method_consistency(self, input_file_path, test_output_path):
        """Test that all transactions have consistent payment method"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # All transactions should be marked as Mercadopago
        assert (result_df["Payment Method"] == "Mercadopago").all()

        # Should have no other payment methods
        unique_methods = result_df["Payment Method"].unique()
        assert len(unique_methods) == 1
        assert unique_methods[0] == "Mercadopago"

    def test_specific_transaction_types(self, input_file_path, test_output_path):
        """Test that specific Mercadopago transaction types are handled correctly"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # Check for expected transaction types
        descriptions = result_df["Description"].unique()

        expected_types = [
            "Movimiento General",
            "Retiro de dinero",
            "Dinero recibido",
            "Ingreso de dinero",
            "Pago",
            "Rendimiento positivo de la inversión",
            "Pago con descuento recibido",
        ]

        for expected_type in expected_types:
            assert any(
                expected_type in desc for desc in descriptions
            ), f"Missing transaction type: {expected_type}"

    def test_sorting_order(self, input_file_path, test_output_path):
        """Test that transactions are sorted chronologically"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # Convert dates to datetime for comparison
        result_df["Date"] = pd.to_datetime(result_df["Date"])

        # Check if dates are in ascending order
        dates = result_df["Date"].tolist()
        assert dates == sorted(dates), "Transactions should be sorted chronologically"

    def test_xlsx_filename_detection(self):
        """Test that Mercadopago XLSX files are detected correctly"""
        # Test various filename patterns
        test_cases = [
            ("mercadopago.xlsx", "Mercadopago"),
            ("MERCADOPAGO.xlsx", "Mercadopago"),
            ("Mercadopago_2025.xlsx", "Mercadopago"),
            ("mercadopago-statement.xlsx", "Mercadopago"),
            ("other-file.xlsx", "Unknown Payment Method"),
            ("santander-account.xlsx", "Unknown Payment Method"),
        ]

        for filename, expected in test_cases:
            result = detect_payment_method(file_path=filename)
            assert (
                result == expected
            ), f"Failed for {filename}: expected {expected}, got {result}"

    def test_input_validation_against_expected(
        self, input_file_path, test_output_path, expected_output_path
    ):
        """Test that generated output matches expected output exactly"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)
        expected_df = pd.read_excel(expected_output_path)

        # Compare row counts
        assert len(result_df) == len(expected_df)

        # Compare column structure
        assert list(result_df.columns) == list(expected_df.columns)

        # Compare total amounts
        result_total = result_df["Amount"].sum()
        expected_total = expected_df["Amount"].sum()
        assert abs(result_total - expected_total) < 0.01

        # Compare currency distribution
        result_ars_count = (result_df["Currency"] == "ARS").sum()
        expected_ars_count = (expected_df["Currency"] == "ARS").sum()
        assert result_ars_count == expected_ars_count

    def test_mercadopago_validation_function(self, input_file_path, test_output_path):
        """Test the Mercadopago-specific validation function"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # Test validation function
        validation_result = validate_mercadopago_balance(
            input_file_path, result_df, "mercadopago.xlsx"
        )

        # Should return input and output totals
        assert "input" in validation_result
        assert "output" in validation_result

        # Totals should match
        assert abs(validation_result["input"] - validation_result["output"]) < 0.01

        # Should match expected total
        assert abs(validation_result["output"] - (-64841.11)) < 0.01

    def test_iso_date_conversion(self, input_file_path, test_output_path):
        """Test that ISO 8601 timestamps are converted correctly"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # All dates should be in YYYY-MM-DD format
        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        assert result_df["Date"].str.match(date_pattern).all()

        # Check specific date conversion
        # Input: "2025-02-01T17:45:36Z" should become "2025-02-01"
        first_date = result_df["Date"].iloc[0]
        assert first_date == "2025-02-01"

    def test_amount_precision_and_variety(self, input_file_path, test_output_path):
        """Test that various amount formats are handled correctly"""
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # Should have both positive and negative amounts
        positive_amounts = result_df[result_df["Amount"] > 0]
        negative_amounts = result_df[result_df["Amount"] < 0]

        assert len(positive_amounts) > 0, "Should have positive amounts"
        assert len(negative_amounts) > 0, "Should have negative amounts"

        # Check for decimal precision
        decimal_amounts = result_df[result_df["Amount"] % 1 != 0]
        assert len(decimal_amounts) > 0, "Should have decimal amounts"

        # Check for large amounts (> 1000000)
        large_amounts = result_df[abs(result_df["Amount"]) > 1000000]
        assert len(large_amounts) > 0, "Should have large amounts"

    def test_output_file_creation(self, input_file_path, test_output_path):
        """Test that output Excel file is created with correct structure"""
        # Ensure output file doesn't exist initially
        if os.path.exists(test_output_path):
            os.remove(test_output_path)

        # Process file
        result_df = parse_mercadopago_xlsx(input_file_path, test_output_path)

        # Verify file was created
        assert os.path.exists(test_output_path)

        # Verify file can be read back
        reloaded_df = pd.read_excel(test_output_path)
        assert len(reloaded_df) == len(result_df)
        assert list(reloaded_df.columns) == list(result_df.columns)

        # Verify data integrity after reload
        assert abs(reloaded_df["Amount"].sum() - result_df["Amount"].sum()) < 0.01
