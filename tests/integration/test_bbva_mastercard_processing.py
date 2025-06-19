import os
import shutil
import tempfile

import pandas as pd
import pytest

from parse_visa_statement import parse_visa_pdf


class TestBBVAMastercardProcessing:
    @pytest.fixture
    def input_pdf_path(self):
        """Path to the test PDF file"""
        return "tests/test_data/input/BBVA-Mastercard-2025-04.pdf"

    @pytest.fixture
    def expected_csv_path(self):
        """Path to the expected output CSV file"""
        return "tests/test_data/expected_output/BBVA-Mastercard-transactions.csv"

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def expected_df(self, expected_csv_path):
        """Load expected data from CSV"""
        return pd.read_csv(expected_csv_path)

    def test_parse_visa_pdf_integration(
        self, input_pdf_path, expected_df, temp_output_dir
    ):
        """Integration test that processes the real PDF and compares with expected output"""
        assert os.path.exists(input_pdf_path), (
            f"Input PDF file not found: {input_pdf_path}"
        )

        output_path = os.path.join(temp_output_dir, "test_output.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        assert os.path.exists(output_path), "Output Excel file was not created"
        assert len(result_df) > 0, "No transactions were parsed"
        assert all(
            col in result_df.columns
            for col in ["Date", "Description", "Currency", "Amount", "Payment Method"]
        ), "Required columns missing from output"

        self._validate_data_integrity(result_df, expected_df)

    def test_transaction_count(self, input_pdf_path, expected_df, temp_output_dir):
        """Test that the correct number of transactions are parsed"""
        output_path = os.path.join(temp_output_dir, "test_count.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        expected_count = len(expected_df)
        actual_count = len(result_df)

        assert actual_count == expected_count, (
            f"Expected {expected_count} transactions, but got {actual_count}"
        )

    def test_currency_handling(self, input_pdf_path, expected_df, temp_output_dir):
        """Test that ARS and USD currencies are handled correctly"""
        output_path = os.path.join(temp_output_dir, "test_currency.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        expected_ars_count = len(expected_df[expected_df["Currency"] == "ARS"])
        expected_usd_count = len(expected_df[expected_df["Currency"] == "USD"])

        actual_ars_count = len(result_df[result_df["Currency"] == "ARS"])
        actual_usd_count = len(result_df[result_df["Currency"] == "USD"])

        assert actual_ars_count == expected_ars_count, (
            f"Expected {expected_ars_count} ARS transactions, got {actual_ars_count}"
        )
        assert actual_usd_count == expected_usd_count, (
            f"Expected {expected_usd_count} USD transactions, got {actual_usd_count}"
        )

        valid_currencies = {"ARS", "USD"}
        actual_currencies = set(result_df["Currency"].unique())
        assert actual_currencies.issubset(valid_currencies), (
            f"Invalid currencies found: {actual_currencies - valid_currencies}"
        )

    def test_amount_totals(self, input_pdf_path, expected_df, temp_output_dir):
        """Test that amount totals match expected values"""
        output_path = os.path.join(temp_output_dir, "test_amounts.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        expected_ars_total = expected_df[expected_df["Currency"] == "ARS"][
            "Amount"
        ].sum()
        expected_usd_total = expected_df[expected_df["Currency"] == "USD"][
            "Amount"
        ].sum()

        actual_ars_total = result_df[result_df["Currency"] == "ARS"]["Amount"].sum()
        actual_usd_total = result_df[result_df["Currency"] == "USD"]["Amount"].sum()

        assert abs(actual_ars_total - expected_ars_total) < 0.01, (
            f"ARS total mismatch: expected {expected_ars_total:.2f}, got {actual_ars_total:.2f}"
        )
        assert abs(actual_usd_total - expected_usd_total) < 0.01, (
            f"USD total mismatch: expected {expected_usd_total:.2f}, got {actual_usd_total:.2f}"
        )

    def test_date_range_and_format(self, input_pdf_path, expected_df, temp_output_dir):
        """Test that dates are in the correct range and format"""
        output_path = os.path.join(temp_output_dir, "test_dates.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        result_dates = pd.to_datetime(result_df["Date"])
        expected_dates = pd.to_datetime(expected_df["Date"])

        expected_min_date = expected_dates.min()
        expected_max_date = expected_dates.max()
        actual_min_date = result_dates.min()
        actual_max_date = result_dates.max()

        assert actual_min_date == expected_min_date, (
            f"Minimum date mismatch: expected {expected_min_date}, got {actual_min_date}"
        )
        assert actual_max_date == expected_max_date, (
            f"Maximum date mismatch: expected {expected_max_date}, got {actual_max_date}"
        )

        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        for date_str in result_df["Date"]:
            assert pd.to_datetime(date_str).strftime("%Y-%m-%d") == date_str, (
                f"Date {date_str} is not in YYYY-MM-DD format"
            )

    def test_payment_method_consistency(self, input_pdf_path, temp_output_dir):
        """Test that all transactions have the correct payment method"""
        output_path = os.path.join(temp_output_dir, "test_payment_method.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        expected_payment_method = "BBVA Mastercard"
        unique_payment_methods = result_df["Payment Method"].unique()

        assert len(unique_payment_methods) == 1, (
            f"Expected only one payment method, got: {unique_payment_methods}"
        )
        assert unique_payment_methods[0] == expected_payment_method, (
            f"Expected payment method '{expected_payment_method}', got '{unique_payment_methods[0]}'"
        )

    def test_specific_transaction_types(
        self, input_pdf_path, expected_df, temp_output_dir
    ):
        """Test specific transaction types are parsed correctly"""
        output_path = os.path.join(temp_output_dir, "test_transaction_types.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        # Test payment transactions
        payment_transactions = result_df[result_df["Description"] == "SU PAGO EN PESOS"]
        expected_payments = expected_df[
            expected_df["Description"] == "SU PAGO EN PESOS"
        ]
        assert len(payment_transactions) == len(expected_payments), (
            f"Expected {len(expected_payments)} payment transactions, got {len(payment_transactions)}"
        )

        # Test that all payment amounts are negative
        for _, payment in payment_transactions.iterrows():
            assert payment["Amount"] < 0, (
                f"Payment transaction should have negative amount, got {payment['Amount']}"
            )

        # Test regular purchase transactions (non-payment transactions)
        purchase_transactions = result_df[
            result_df["Description"] != "SU PAGO EN PESOS"
        ]
        expected_purchases = expected_df[
            expected_df["Description"] != "SU PAGO EN PESOS"
        ]
        assert len(purchase_transactions) == len(expected_purchases), (
            f"Expected {len(expected_purchases)} purchase transactions, got {len(purchase_transactions)}"
        )

        # Test that all purchase amounts are positive
        for _, purchase in purchase_transactions.iterrows():
            assert purchase["Amount"] > 0, (
                f"Purchase transaction should have positive amount, got {purchase['Amount']}"
            )

    def test_negative_amounts(self, input_pdf_path, expected_df, temp_output_dir):
        """Test that payments have negative amounts and purchases have positive amounts"""
        output_path = os.path.join(temp_output_dir, "test_negative_amounts.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        # Test payment transactions have negative amounts
        payments = result_df[result_df["Description"] == "SU PAGO EN PESOS"]
        for _, payment in payments.iterrows():
            assert payment["Amount"] < 0, (
                f"Payment transaction should have negative amount, got {payment['Amount']}"
            )

        # Test purchase transactions have positive amounts
        purchases = result_df[result_df["Description"] != "SU PAGO EN PESOS"]
        for _, purchase in purchases.iterrows():
            assert purchase["Amount"] > 0, (
                f"Purchase transaction should have positive amount, got {purchase['Amount']}"
            )

    def test_date_format_handling(self, input_pdf_path, temp_output_dir):
        """Test that DD-MMM-YY date format is handled correctly for BBVA Mastercard"""
        output_path = os.path.join(temp_output_dir, "test_date_format.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        # All dates should be in YYYY-MM-DD format
        for date_str in result_df["Date"]:
            assert pd.to_datetime(date_str), f"Date {date_str} is not a valid date"
            formatted_date = pd.to_datetime(date_str).strftime("%Y-%m-%d")
            assert date_str == formatted_date, (
                f"Date {date_str} is not in YYYY-MM-DD format"
            )

        # Test specific date ranges for BBVA Mastercard (March-April 2025)
        result_dates = pd.to_datetime(result_df["Date"])
        min_date = result_dates.min()
        max_date = result_dates.max()

        # Should be in 2025
        assert min_date.year == 2025, f"Expected year 2025, got {min_date.year}"
        assert max_date.year == 2025, f"Expected year 2025, got {max_date.year}"

        # Should be in March-April range
        assert min_date.month >= 3, f"Expected month >= 3, got {min_date.month}"
        assert max_date.month <= 4, f"Expected month <= 4, got {max_date.month}"

    def test_merchant_name_parsing(self, input_pdf_path, expected_df, temp_output_dir):
        """Test that merchant names are parsed correctly from BBVA Mastercard format"""
        output_path = os.path.join(temp_output_dir, "test_merchants.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        # Test specific merchant patterns expected in BBVA Mastercard
        expected_merchants = [
            "ON FIT",
            "MERPAGO*MCDONALDS",
            "MI GUSTO",
            "MERPAGO*SCANNAPIECO",
            "ASUMARE PALERMO",
            "MERPAGO*MCDONALDSECOMM",
        ]

        for merchant in expected_merchants:
            merchant_transactions = result_df[
                result_df["Description"].str.contains(merchant, na=False)
            ]
            expected_merchant_transactions = expected_df[
                expected_df["Description"].str.contains(merchant, na=False)
            ]
            assert len(merchant_transactions) == len(expected_merchant_transactions), (
                f"Mismatch in {merchant} transactions: expected {len(expected_merchant_transactions)}, got {len(merchant_transactions)}"
            )

    def test_amount_precision(self, input_pdf_path, expected_df, temp_output_dir):
        """Test that amounts are parsed with correct precision"""
        output_path = os.path.join(temp_output_dir, "test_precision.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        # Check that specific expected amounts are present
        expected_amounts = [107970.0, 4000.0, 21000.0, 9500.0, 39500.0, 3200.0]
        actual_positive_amounts = sorted(
            result_df[result_df["Amount"] > 0]["Amount"].tolist()
        )

        assert len(actual_positive_amounts) == len(expected_amounts), (
            f"Expected {len(expected_amounts)} positive amounts, got {len(actual_positive_amounts)}"
        )

        for expected, actual in zip(sorted(expected_amounts), actual_positive_amounts):
            assert abs(actual - expected) < 0.01, (
                f"Amount precision error: expected {expected}, got {actual}"
            )

    def _validate_data_integrity(self, result_df, expected_df):
        """Validate overall data integrity without strict row-by-row comparison"""
        assert len(result_df) == len(expected_df), (
            f"Transaction count mismatch: expected {len(expected_df)}, got {len(result_df)}"
        )

        # Validate currency distribution
        expected_ars_count = len(expected_df[expected_df["Currency"] == "ARS"])
        expected_usd_count = len(expected_df[expected_df["Currency"] == "USD"])
        actual_ars_count = len(result_df[result_df["Currency"] == "ARS"])
        actual_usd_count = len(result_df[result_df["Currency"] == "USD"])

        assert actual_ars_count == expected_ars_count, (
            f"ARS transaction count mismatch: expected {expected_ars_count}, got {actual_ars_count}"
        )
        assert actual_usd_count == expected_usd_count, (
            f"USD transaction count mismatch: expected {expected_usd_count}, got {actual_usd_count}"
        )

        # Validate amount totals
        expected_ars_total = expected_df[expected_df["Currency"] == "ARS"][
            "Amount"
        ].sum()
        expected_usd_total = expected_df[expected_df["Currency"] == "USD"][
            "Amount"
        ].sum()
        actual_ars_total = result_df[result_df["Currency"] == "ARS"]["Amount"].sum()
        actual_usd_total = result_df[result_df["Currency"] == "USD"]["Amount"].sum()

        assert abs(actual_ars_total - expected_ars_total) < 0.01, (
            f"ARS total mismatch: expected {expected_ars_total:.2f}, got {actual_ars_total:.2f}"
        )
        assert abs(actual_usd_total - expected_usd_total) < 0.01, (
            f"USD total mismatch: expected {expected_usd_total:.2f}, got {actual_usd_total:.2f}"
        )

        # Validate date ranges
        result_dates = pd.to_datetime(result_df["Date"])
        expected_dates = pd.to_datetime(expected_df["Date"])

        assert result_dates.min() == expected_dates.min(), (
            f"Min date mismatch: expected {expected_dates.min()}, got {result_dates.min()}"
        )
        assert result_dates.max() == expected_dates.max(), (
            f"Max date mismatch: expected {expected_dates.max()}, got {result_dates.max()}"
        )

        # Validate payment method consistency
        expected_payment_method = "BBVA Mastercard"
        unique_payment_methods = result_df["Payment Method"].unique()
        assert len(unique_payment_methods) == 1, (
            f"Expected only one payment method, got: {unique_payment_methods}"
        )
        assert unique_payment_methods[0] == expected_payment_method, (
            f"Expected payment method '{expected_payment_method}', got '{unique_payment_methods[0]}'"
        )

        # Validate special transaction types
        payment_transactions = result_df[result_df["Description"] == "SU PAGO EN PESOS"]
        expected_payments = expected_df[
            expected_df["Description"] == "SU PAGO EN PESOS"
        ]
        assert len(payment_transactions) == len(expected_payments), (
            f"Payment transaction count mismatch: expected {len(expected_payments)}, got {len(payment_transactions)}"
        )
