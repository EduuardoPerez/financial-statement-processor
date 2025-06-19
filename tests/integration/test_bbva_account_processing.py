import os
import tempfile
import unittest

import pandas as pd

from parse_visa_statement import detect_payment_method, parse_account_xls


class TestBBVAAccountProcessing(unittest.TestCase):
    """Integration tests for BBVA Account XLS processing end-to-end workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_xls_path = (
            "tests/test_data/input/BBVA-Account-Detalle_mov_cuenta_07_06_2025.xls"
        )
        self.expected_csv_path = (
            "tests/test_data/expected_output/BBVA-Account-transactions.csv"
        )
        self.expected_xlsx_path = (
            "tests/test_data/expected_output/BBVA-Account-transactions.xlsx"
        )

        # Create temporary output file
        self.temp_output = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        self.temp_output_path = self.temp_output.name
        self.temp_output.close()

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_output_path):
            os.unlink(self.temp_output_path)

    def test_parse_account_xls_integration(self):
        """Test complete BBVA Account XLS processing workflow"""
        # Process the XLS file
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)

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
        """Test that BBVA Account processing captures the correct number of transactions"""
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)
        expected_df = pd.read_excel(self.expected_xlsx_path)

        self.assertEqual(
            len(result_df), 60, "Should process exactly 60 BBVA Account transactions"
        )
        self.assertEqual(
            len(result_df), len(expected_df), "Should match expected transaction count"
        )

    def test_currency_handling(self):
        """Test that BBVA Account transactions are correctly identified as ARS"""
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)

        # All BBVA Account transactions should be ARS
        ars_count = len(result_df[result_df["Currency"] == "ARS"])
        usd_count = len(result_df[result_df["Currency"] == "USD"])

        self.assertEqual(ars_count, 60, "All BBVA Account transactions should be ARS")
        self.assertEqual(usd_count, 0, "No USD transactions expected in BBVA Account")

    def test_amount_totals(self):
        """Test that amount totals match expected values"""
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)
        expected_df = pd.read_excel(self.expected_xlsx_path)

        result_total = result_df["Amount"].sum()
        expected_total = expected_df["Amount"].sum()

        # Both should be essentially zero (within floating point precision)
        self.assertAlmostEqual(
            result_total,
            expected_total,
            places=6,
            msg="Amount totals should match expected values",
        )
        self.assertLess(abs(result_total), 1e-6, "Total should be essentially zero")

    def test_date_range_and_format(self):
        """Test date parsing and format conversion"""
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)

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

    def test_payment_method_consistency(self):
        """Test that all transactions are correctly labeled as BBVA Account"""
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)

        # All payment methods should be "BBVA Account"
        payment_methods = result_df["Payment Method"].unique()
        self.assertEqual(len(payment_methods), 1, "Should have only one payment method")
        self.assertEqual(
            payment_methods[0],
            "BBVA Account",
            "Payment method should be 'BBVA Account'",
        )

    def test_specific_transaction_types(self):
        """Test parsing of specific BBVA Account transaction types"""
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)

        # Check for specific transaction types common in BBVA Account statements
        descriptions = result_df["Description"].str.upper()

        # Look for transfers
        transfers = descriptions.str.contains("TRANSFERENCIA", na=False)
        self.assertGreater(transfers.sum(), 0, "Should contain transfer transactions")

        # Look for card payments
        card_payments = descriptions.str.contains(
            "CUENTA VISA|CUENTA MASTERCARD", na=False
        )
        self.assertGreater(
            card_payments.sum(), 0, "Should contain card payment transactions"
        )

        # Look for interest transactions
        interest = descriptions.str.contains("INTERESES", na=False)
        self.assertGreater(interest.sum(), 0, "Should contain interest transactions")

    def test_european_number_format_handling(self):
        """Test that European number format is correctly converted"""
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)

        # Check that we have both positive and negative amounts
        positive_amounts = result_df[result_df["Amount"] > 0]
        negative_amounts = result_df[result_df["Amount"] < 0]

        self.assertGreater(len(positive_amounts), 0, "Should have positive amounts")
        self.assertGreater(len(negative_amounts), 0, "Should have negative amounts")

        # Check for amounts that would come from European format
        # (should have decimal precision)
        decimal_amounts = result_df[result_df["Amount"] % 1 != 0]
        self.assertGreater(
            len(decimal_amounts), 0, "Should have amounts with decimal places"
        )

    def test_sorting_order(self):
        """Test that transactions are sorted in descending date order (newest first)"""
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)
        expected_df = pd.read_excel(self.expected_xlsx_path)

        # Convert to datetime for comparison
        result_dates = pd.to_datetime(result_df["Date"])

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
        """Test that BBVA Account is correctly detected from XLS filename"""
        # Test with the actual filename
        payment_method = detect_payment_method(file_path=self.test_xls_path)
        self.assertEqual(
            payment_method,
            "BBVA Account",
            "Should detect BBVA Account from XLS filename",
        )

        # Test with variations of BBVA Account filenames
        test_filenames = [
            "BBVA-Account-statement.xls",
            "bbva-account-detalle.xls",
            "BBVA-DETALLE-movements.xls",
            "account-bbva-detalle.xls",
        ]

        for filename in test_filenames:
            payment_method = detect_payment_method(file_path=filename)
            self.assertEqual(
                payment_method,
                "BBVA Account",
                f"Should detect BBVA Account from filename: {filename}",
            )

    def test_column_structure(self):
        """Test that output has correct column structure"""
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)
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
        result_df = parse_account_xls(self.test_xls_path, self.temp_output_path)
        expected_df = pd.read_excel(self.expected_xlsx_path)

        # Compare key metrics
        self.assertEqual(len(result_df), len(expected_df), "Row count should match")
        self.assertAlmostEqual(
            result_df["Amount"].sum(),
            expected_df["Amount"].sum(),
            places=6,
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


if __name__ == "__main__":
    unittest.main()
