import unittest
import pandas as pd
import os
import tempfile
from parse_visa_statement import parse_macro_account_xls, detect_payment_method


class TestMacroAccountProcessing(unittest.TestCase):
    """Integration tests for Macro Account XLS processing end-to-end workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_xls_path = "tests/test_data/input/MACRO-movimientos-de-cuenta.xls"
        self.expected_csv_path = (
            "tests/test_data/expected_output/Macro-Account-transactions.csv"
        )
        self.expected_xlsx_path = (
            "tests/test_data/expected_output/Macro-Account-transactions.xlsx"
        )

        # Create temporary output file
        self.temp_output = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        self.temp_output_path = self.temp_output.name
        self.temp_output.close()

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_output_path):
            os.unlink(self.temp_output_path)

    def test_parse_macro_account_xls_integration(self):
        """Test complete Macro Account XLS processing workflow"""
        # Process the XLS file
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)

        # Verify output file was created
        self.assertTrue(
            os.path.exists(self.temp_output_path), "Output file should be created"
        )

        # Load expected results
        expected_df = pd.read_excel(self.expected_xlsx_path)

        # Verify DataFrame is not empty
        self.assertGreater(len(result_df), 0, "Result DataFrame should not be empty")

        # Compare with expected results
        self.assertEqual(
            len(result_df), len(expected_df), "Transaction count should match expected"
        )

    def test_transaction_count(self):
        """Test that Macro Account processing captures the correct number of transactions"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)
        expected_df = pd.read_excel(self.expected_xlsx_path)

        self.assertEqual(
            len(result_df), 37, "Should process exactly 37 Macro Account transactions"
        )
        self.assertEqual(
            len(result_df), len(expected_df), "Should match expected transaction count"
        )

    def test_currency_handling(self):
        """Test that Macro Account transactions are correctly identified as ARS"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)

        # All Macro Account transactions should be ARS
        ars_count = len(result_df[result_df["Currency"] == "ARS"])
        usd_count = len(result_df[result_df["Currency"] == "USD"])

        self.assertEqual(ars_count, 37, "All Macro Account transactions should be ARS")
        self.assertEqual(usd_count, 0, "No USD transactions expected in Macro Account")

    def test_amount_totals(self):
        """Test that amount totals match expected values"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)
        expected_df = pd.read_excel(self.expected_xlsx_path)

        result_total = result_df["Amount"].sum()
        expected_total = expected_df["Amount"].sum()

        # Should sum to exactly 34,122.00
        self.assertAlmostEqual(
            result_total,
            34122.00,
            places=2,
            msg="Amount total should be 34,122.00",
        )
        self.assertAlmostEqual(
            result_total,
            expected_total,
            places=2,
            msg="Amount totals should match expected values",
        )

    def test_date_range_and_format(self):
        """Test date parsing and format conversion"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)

        # Convert dates to datetime for analysis
        dates = pd.to_datetime(result_df["Date"])

        # Verify date range (should be from February to June 2025)
        earliest_date = dates.min()
        latest_date = dates.max()

        self.assertGreaterEqual(
            earliest_date.year, 2025, "Earliest date should be 2025 or later"
        )
        self.assertLessEqual(
            latest_date.year, 2025, "Latest date should be 2025 or earlier"
        )

        # Verify date format is YYYY-MM-DD
        for date_str in result_df["Date"]:
            self.assertRegex(
                date_str, r"^\d{4}-\d{2}-\d{2}$", "Date should be in YYYY-MM-DD format"
            )

        # Verify specific date range for Macro Account
        self.assertEqual(
            earliest_date.strftime("%Y-%m-%d"),
            "2025-02-07",
            "Earliest date should be 2025-02-07",
        )
        self.assertEqual(
            latest_date.strftime("%Y-%m-%d"),
            "2025-06-06",
            "Latest date should be 2025-06-06",
        )

    def test_payment_method_consistency(self):
        """Test that all transactions are correctly labeled as Macro Account"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)

        # All payment methods should be "Macro Account"
        payment_methods = result_df["Payment Method"].unique()
        self.assertEqual(len(payment_methods), 1, "Should have only one payment method")
        self.assertEqual(
            payment_methods[0],
            "Macro Account",
            "Payment method should be 'Macro Account'",
        )

    def test_specific_transaction_types(self):
        """Test parsing of specific Macro Account transaction types"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)

        # Check for specific transaction types common in Macro Account statements
        descriptions = result_df["Description"].str.upper()

        # Look for compensations
        compensations = descriptions.str.contains("COMPENSACION", na=False)
        self.assertGreater(
            compensations.sum(), 0, "Should contain compensation transactions"
        )

        # Look for transfers
        transfers = descriptions.str.contains("TRANSF:", na=False)
        self.assertGreater(transfers.sum(), 0, "Should contain transfer transactions")

        # Look for credit card payments
        card_payments = descriptions.str.contains("TARJETA DE CREDITO", na=False)
        self.assertGreater(
            card_payments.sum(), 0, "Should contain credit card payment transactions"
        )

        # Look for commissions
        commissions = descriptions.str.contains("COMISION", na=False)
        self.assertGreater(
            commissions.sum(), 0, "Should contain commission transactions"
        )

        # Look for capitalization/interest
        capitalization = descriptions.str.contains("CAPITALIZACION", na=False)
        self.assertGreater(
            capitalization.sum(), 0, "Should contain capitalization transactions"
        )

    def test_amount_precision_and_variety(self):
        """Test that amounts are parsed with correct precision and variety"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)

        # Check that we have both positive and negative amounts
        positive_amounts = result_df[result_df["Amount"] > 0]
        negative_amounts = result_df[result_df["Amount"] < 0]

        self.assertGreater(len(positive_amounts), 0, "Should have positive amounts")
        self.assertGreater(len(negative_amounts), 0, "Should have negative amounts")

        # Check for amounts with decimal precision
        decimal_amounts = result_df[result_df["Amount"] % 1 != 0]
        self.assertGreater(
            len(decimal_amounts), 0, "Should have amounts with decimal places"
        )

        # Check for large amounts (credit card transactions)
        large_amounts = result_df[abs(result_df["Amount"]) > 100000]
        self.assertGreater(
            len(large_amounts), 0, "Should have large transaction amounts"
        )

    def test_sorting_order(self):
        """Test that transactions are sorted in descending date order (newest first)"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)
        expected_df = pd.read_excel(self.expected_xlsx_path)

        # Convert to datetime for comparison
        result_dates = pd.to_datetime(result_df["Date"])
        expected_dates = pd.to_datetime(expected_df["Date"])

        # Check that dates are in descending order
        is_sorted = result_dates.is_monotonic_decreasing
        self.assertTrue(
            is_sorted, "Dates should be sorted in descending order (newest first)"
        )

        # Compare first and last dates with expected
        self.assertEqual(
            result_df["Date"].iloc[0],
            expected_df["Date"].iloc[0],
            "First transaction date should match expected",
        )
        self.assertEqual(
            result_df["Date"].iloc[-1],
            expected_df["Date"].iloc[-1],
            "Last transaction date should match expected",
        )

    def test_xls_filename_detection(self):
        """Test that Macro Account is correctly detected from XLS filename"""
        # Test with the actual filename
        payment_method = detect_payment_method(file_path=self.test_xls_path)
        self.assertEqual(
            payment_method,
            "Macro Account",
            "Should detect Macro Account from XLS filename",
        )

        # Test with variations of Macro Account filenames
        test_filenames = [
            "MACRO-movimientos-de-cuenta.xls",
            "macro-movimientos-statement.xls",
            "MACRO-MOVIMIENTOS-detalle.xls",
            "movimientos-macro-cuenta.xls",
        ]

        for filename in test_filenames:
            payment_method = detect_payment_method(file_path=filename)
            self.assertEqual(
                payment_method,
                "Macro Account",
                f"Should detect Macro Account from filename: {filename}",
            )

    def test_column_structure(self):
        """Test that output has correct column structure"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)
        expected_df = pd.read_excel(self.expected_xlsx_path)

        # Check column names
        expected_columns = [
            "Date",
            "Description",
            "Currency",
            "Amount",
            "Payment Method",
        ]
        self.assertEqual(
            list(result_df.columns),
            expected_columns,
            "Columns should match expected structure",
        )
        self.assertEqual(
            list(result_df.columns),
            list(expected_df.columns),
            "Columns should match expected output",
        )

        # Check data types
        self.assertTrue(
            result_df["Amount"].dtype in ["float64", "int64"],
            "Amount should be numeric",
        )
        self.assertEqual(
            result_df["Currency"].dtype, "object", "Currency should be string"
        )
        self.assertEqual(
            result_df["Payment Method"].dtype,
            "object",
            "Payment Method should be string",
        )

    def test_input_validation_against_expected(self):
        """Test that our output exactly matches the expected output"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)
        expected_df = pd.read_excel(self.expected_xlsx_path)

        # Compare key metrics
        self.assertEqual(len(result_df), len(expected_df), "Row count should match")
        self.assertAlmostEqual(
            result_df["Amount"].sum(),
            expected_df["Amount"].sum(),
            places=2,
            msg="Amount totals should match",
        )

        # Compare first few transactions in detail
        for i in range(min(5, len(result_df))):
            result_row = result_df.iloc[i]
            expected_row = expected_df.iloc[i]

            self.assertEqual(
                result_row["Date"],
                expected_row["Date"],
                f"Date should match for row {i}",
            )
            self.assertEqual(
                result_row["Description"],
                expected_row["Description"],
                f"Description should match for row {i}",
            )
            self.assertEqual(
                result_row["Currency"],
                expected_row["Currency"],
                f"Currency should match for row {i}",
            )
            self.assertAlmostEqual(
                result_row["Amount"],
                expected_row["Amount"],
                places=2,
                msg=f"Amount should match for row {i}",
            )
            self.assertEqual(
                result_row["Payment Method"],
                expected_row["Payment Method"],
                f"Payment Method should match for row {i}",
            )

    def test_source_balance_validation(self):
        """Test that the sum matches the source balance from the XLS file"""
        result_df = parse_macro_account_xls(self.test_xls_path, self.temp_output_path)

        # Read the source XLS to get the balance from first row Saldo column
        source_df = pd.read_excel(self.test_xls_path, header=None)
        source_balance = source_df.iloc[3, 4]  # First data row, Saldo column

        computed_sum = result_df["Amount"].sum()

        self.assertAlmostEqual(
            computed_sum,
            source_balance,
            places=2,
            msg=f"Computed sum {computed_sum} should match source balance {source_balance}",
        )

        # Should be exactly 34,122.00
        self.assertEqual(source_balance, 34122.0, "Source balance should be 34,122.00")


if __name__ == "__main__":
    unittest.main()
