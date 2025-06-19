import pandas as pd

from parse_visa_statement import (
    detect_payment_method,
    parse_bbva_visa_csv,
    validate_csv_balance,
)


class TestBBVAVisaCSVProcessing:
    """Test BBVA VISA CSV file processing (both Autorizaciones and Movimientos)"""

    def test_bbva_visa_auth_csv_processing_workflow(self, tmp_path):
        """Test complete workflow for BBVA VISA Autorizaciones CSV processing"""
        # Input and output paths
        input_path = "tests/test_data/input/BBVA-Visa-Autorizaciones.csv"
        output_path = tmp_path / "BBVA-Visa-auth-test.xlsx"
        expected_path = (
            "tests/test_data/expected_output/BBVA-Visa-auth-transactions.xlsx"
        )

        # Process the CSV file
        result_df = parse_bbva_visa_csv(str(input_path), str(output_path), "auth")

        # Load expected results
        expected_df = pd.read_excel(expected_path)

        # Verify basic properties
        assert len(result_df) == len(expected_df)
        assert len(result_df) == 2
        assert list(result_df.columns) == list(expected_df.columns)

        # Verify transaction data
        assert result_df["Date"].tolist() == expected_df["Date"].tolist()
        assert result_df["Description"].tolist() == expected_df["Description"].tolist()
        assert result_df["Currency"].tolist() == expected_df["Currency"].tolist()
        assert result_df["Amount"].tolist() == expected_df["Amount"].tolist()
        assert (
            result_df["Payment Method"].tolist()
            == expected_df["Payment Method"].tolist()
        )

        # Verify amounts
        assert result_df["Amount"].sum() == 20189.34
        assert all(result_df["Currency"] == "ARS")
        assert all(result_df["Payment Method"] == "BBVA VISA")

        # Verify dates are properly formatted
        assert all(pd.to_datetime(result_df["Date"], format="%Y-%m-%d"))

    def test_bbva_visa_movs_csv_processing_workflow(self, tmp_path):
        """Test complete workflow for BBVA VISA Movimientos CSV processing"""
        # Input and output paths
        input_path = "tests/test_data/input/BBVA-Visa-Movimientos.csv"
        output_path = tmp_path / "BBVA-Visa-movs-test.xlsx"
        expected_path = (
            "tests/test_data/expected_output/BBVA-Visa-movs-transactions.xlsx"
        )

        # Process the CSV file
        result_df = parse_bbva_visa_csv(str(input_path), str(output_path), "movs")

        # Load expected results
        expected_df = pd.read_excel(expected_path)

        # Verify basic properties
        assert len(result_df) == len(expected_df)
        assert len(result_df) == 15
        assert list(result_df.columns) == list(expected_df.columns)

        # Verify transaction data matches exactly
        assert result_df["Date"].tolist() == expected_df["Date"].tolist()
        assert result_df["Description"].tolist() == expected_df["Description"].tolist()
        assert result_df["Currency"].tolist() == expected_df["Currency"].tolist()
        assert result_df["Amount"].tolist() == expected_df["Amount"].tolist()
        assert (
            result_df["Payment Method"].tolist()
            == expected_df["Payment Method"].tolist()
        )

        # Verify currency distribution
        ars_transactions = result_df[result_df["Currency"] == "ARS"]
        usd_transactions = result_df[result_df["Currency"] == "USD"]
        assert len(ars_transactions) == 14
        assert len(usd_transactions) == 1

        # Verify amounts
        assert usd_transactions["Amount"].sum() == 8.53
        assert all(result_df["Payment Method"] == "BBVA VISA")

        # Verify negative payment amount
        payment_transactions = result_df[result_df["Description"] == "SU PAGO EN PESOS"]
        assert len(payment_transactions) == 1
        assert payment_transactions["Amount"].iloc[0] == -1010605.89

    def test_bbva_visa_csv_validation_auth(self):
        """Test CSV balance validation for BBVA VISA Autorizaciones"""
        input_path = "tests/test_data/input/BBVA-Visa-Autorizaciones.csv"

        # Process file to get DataFrame
        result_df = parse_bbva_visa_csv(input_path, "/tmp/test.xlsx", "auth")

        # Validate balance
        validation_result = validate_csv_balance(input_path, result_df, "test-file.csv")

        # Check validation results
        assert validation_result["input"] == 20189.34
        assert validation_result["output"] == 20189.34
        assert abs(validation_result["input"] - validation_result["output"]) < 0.01

    def test_bbva_visa_csv_validation_movs(self):
        """Test CSV balance validation for BBVA VISA Movimientos"""
        input_path = "tests/test_data/input/BBVA-Visa-Movimientos.csv"

        # Process file to get DataFrame
        result_df = parse_bbva_visa_csv(input_path, "/tmp/test.xlsx", "movs")

        # Validate balance
        validation_result = validate_csv_balance(input_path, result_df, "test-file.csv")

        # Check validation results (includes negative payment)
        expected_total = -590831.30  # As shown in the validation output
        assert abs(validation_result["input"] - expected_total) < 0.01
        assert abs(validation_result["output"] - expected_total) < 0.01

    def test_bbva_visa_csv_date_conversion_auth(self):
        """Test date conversion for BBVA VISA Autorizaciones (DD/MM/YYYY -> YYYY-MM-DD)"""
        input_path = "tests/test_data/input/BBVA-Visa-Autorizaciones.csv"
        result_df = parse_bbva_visa_csv(input_path, "/tmp/test.xlsx", "auth")

        # All transactions should be on 2025-06-13
        expected_dates = ["2025-06-13", "2025-06-13"]
        assert result_df["Date"].tolist() == expected_dates

    def test_bbva_visa_csv_date_conversion_movs(self):
        """Test date conversion for BBVA VISA Movimientos (DD/MM/YYYY -> YYYY-MM-DD)"""
        input_path = "tests/test_data/input/BBVA-Visa-Movimientos.csv"
        result_df = parse_bbva_visa_csv(input_path, "/tmp/test.xlsx", "movs")

        # Verify date range and format
        dates = pd.to_datetime(result_df["Date"])
        assert dates.min() == pd.Timestamp("2025-06-01")
        assert dates.max() == pd.Timestamp("2025-06-13")

        # Verify dates are properly formatted as YYYY-MM-DD
        for date_str in result_df["Date"]:
            assert pd.to_datetime(date_str, format="%Y-%m-%d")

    def test_bbva_visa_csv_currency_mapping_auth(self):
        """Test currency mapping for BBVA VISA Autorizaciones (Pesos -> ARS)"""
        input_path = "tests/test_data/input/BBVA-Visa-Autorizaciones.csv"
        result_df = parse_bbva_visa_csv(input_path, "/tmp/test.xlsx", "auth")

        # All should be ARS
        assert all(result_df["Currency"] == "ARS")

    def test_bbva_visa_csv_currency_mapping_movs(self):
        """Test currency mapping for BBVA VISA Movimientos (Pesos -> ARS, Dolares -> USD)"""
        input_path = "tests/test_data/input/BBVA-Visa-Movimientos.csv"
        result_df = parse_bbva_visa_csv(input_path, "/tmp/test.xlsx", "movs")

        # Check currency distribution
        currencies = result_df["Currency"].value_counts()
        assert currencies["ARS"] == 14
        assert currencies["USD"] == 1

    def test_bbva_visa_csv_payment_method_consistency(self):
        """Test that payment method is consistently set to 'BBVA VISA'"""
        # Test both file types
        auth_path = "tests/test_data/input/BBVA-Visa-Autorizaciones.csv"
        movs_path = "tests/test_data/input/BBVA-Visa-Movimientos.csv"

        auth_df = parse_bbva_visa_csv(auth_path, "/tmp/test1.xlsx", "auth")
        movs_df = parse_bbva_visa_csv(movs_path, "/tmp/test2.xlsx", "movs")

        assert all(auth_df["Payment Method"] == "BBVA VISA")
        assert all(movs_df["Payment Method"] == "BBVA VISA")

    def test_bbva_visa_csv_detection(self):
        """Test CSV filename-based detection for BBVA VISA files"""
        auth_path = "tests/test_data/input/BBVA-Visa-Autorizaciones.csv"
        movs_path = "tests/test_data/input/BBVA-Visa-Movimientos.csv"

        assert detect_payment_method(file_path=auth_path) == "BBVA VISA"
        assert detect_payment_method(file_path=movs_path) == "BBVA VISA"

    def test_bbva_visa_csv_european_number_format(self):
        """Test European number format handling (comma removal)"""
        input_path = "tests/test_data/input/BBVA-Visa-Autorizaciones.csv"
        result_df = parse_bbva_visa_csv(input_path, "/tmp/test.xlsx", "auth")

        # Verify specific amounts were converted correctly
        amounts = result_df["Amount"].tolist()
        assert 4940.0 in amounts  # From "4,940.00"
        assert 15249.34 in amounts  # From "15,249.34"

    def test_bbva_visa_csv_output_file_creation(self, tmp_path):
        """Test that output Excel files are created correctly"""
        input_path = "tests/test_data/input/BBVA-Visa-Autorizaciones.csv"
        output_path = tmp_path / "test_output.xlsx"

        parse_bbva_visa_csv(str(input_path), str(output_path), "auth")

        # Verify file was created
        assert output_path.exists()

        # Verify file can be read back
        df = pd.read_excel(output_path)
        assert len(df) == 2
        assert "Date" in df.columns
        assert "Description" in df.columns
        assert "Currency" in df.columns
        assert "Amount" in df.columns
        assert "Payment Method" in df.columns
