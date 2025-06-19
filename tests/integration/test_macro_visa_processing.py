import os
import shutil
import tempfile

import pandas as pd
import pytest

from parse_visa_statement import parse_visa_pdf


class TestMacroVisaProcessing:
    @pytest.fixture
    def input_pdf_path(self):
        """Path to the test PDF file"""
        return "tests/test_data/input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"

    @pytest.fixture
    def expected_csv_path(self):
        """Path to the expected output CSV file"""
        return "tests/test_data/expected_output/MACRO-VISA-transactions.csv"

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

        expected_payment_method = "Macro VISA"
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

        payment_transactions = result_df[result_df["Description"] == "SU PAGO EN PESOS"]
        expected_payments = expected_df[
            expected_df["Description"] == "SU PAGO EN PESOS"
        ]
        assert len(payment_transactions) == len(expected_payments), (
            f"Expected {len(expected_payments)} payment transactions, got {len(payment_transactions)}"
        )

        adjustment_transactions = result_df[
            result_df["Description"] == "AJUSTE P/DESCNTO. EN COMERCIO"
        ]
        expected_adjustments = expected_df[
            expected_df["Description"] == "AJUSTE P/DESCNTO. EN COMERCIO"
        ]
        assert len(adjustment_transactions) == len(expected_adjustments), (
            f"Expected {len(expected_adjustments)} adjustment transactions, got {len(adjustment_transactions)}"
        )

        tax_keywords = ["IMPUESTO", "IIBB", "IVA", "DB.RG", "DB.IMPUESTO"]
        for keyword in tax_keywords:
            result_tax = result_df[
                result_df["Description"].str.contains(keyword, na=False)
            ]
            expected_tax = expected_df[
                expected_df["Description"].str.contains(keyword, na=False)
            ]
            assert len(result_tax) == len(expected_tax), (
                f"Mismatch in {keyword} transactions: expected {len(expected_tax)}, got {len(result_tax)}"
            )

    def test_negative_amounts(self, input_pdf_path, expected_df, temp_output_dir):
        """Test that payments and adjustments have negative amounts"""
        output_path = os.path.join(temp_output_dir, "test_negative_amounts.xlsx")
        result_df = parse_visa_pdf(input_pdf_path, output_path)

        payments = result_df[result_df["Description"] == "SU PAGO EN PESOS"]
        for _, payment in payments.iterrows():
            assert payment["Amount"] < 0, (
                f"Payment transaction should have negative amount, got {payment['Amount']}"
            )

        adjustments = result_df[
            result_df["Description"] == "AJUSTE P/DESCNTO. EN COMERCIO"
        ]
        for _, adjustment in adjustments.iterrows():
            assert adjustment["Amount"] < 0, (
                f"Adjustment transaction should have negative amount, got {adjustment['Amount']}"
            )

    def _validate_data_integrity(self, result_df, expected_df):
        """Validate overall data integrity without strict row-by-row comparison"""
        assert len(result_df) == len(expected_df), (
            f"Transaction count mismatch: expected {len(expected_df)}, got {len(result_df)}"
        )

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

        result_dates = pd.to_datetime(result_df["Date"])
        expected_dates = pd.to_datetime(expected_df["Date"])

        assert result_dates.min() == expected_dates.min(), (
            f"Min date mismatch: expected {expected_dates.min()}, got {result_dates.min()}"
        )
        assert result_dates.max() == expected_dates.max(), (
            f"Max date mismatch: expected {expected_dates.max()}, got {result_dates.max()}"
        )

        special_descriptions = ["SU PAGO EN PESOS", "AJUSTE P/DESCNTO. EN COMERCIO"]
        for desc in special_descriptions:
            expected_count = len(expected_df[expected_df["Description"] == desc])
            actual_count = len(result_df[result_df["Description"] == desc])
            assert actual_count == expected_count, (
                f"Special transaction '{desc}' count mismatch: expected {expected_count}, got {actual_count}"
            )
