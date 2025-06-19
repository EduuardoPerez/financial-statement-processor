
import pandas as pd

from parse_visa_statement import print_processing_summary


class TestPrintProcessingSummary:
    """Unit tests for the print_processing_summary function"""

    def test_print_processing_summary_basic(self, capsys):
        """Test print_processing_summary with basic data"""
        # Create sample DataFrame
        data = [
            {
                "Date": "2022-12-01",
                "Description": "Test Transaction",
                "Currency": "ARS",
                "Amount": 1000.50,
            },
            {
                "Date": "2022-12-02",
                "Description": "USD Transaction",
                "Currency": "USD",
                "Amount": 10.25,
            },
        ]
        df = pd.DataFrame(data)

        reported_balance = {"ars": 1000.50, "usd": 10.25}
        computed_balance = {"ars": 1000.50, "usd": 10.25}

        print_processing_summary(
            "test_file.pdf", df, reported_balance, computed_balance, "output.xlsx"
        )

        captured = capsys.readouterr()
        assert "PROCESSING SUMMARY: test_file.pdf" in captured.out
        assert "Transactions Processed: 2" in captured.out
        assert "Output File: output.xlsx" in captured.out
        assert "ARS: 1,000.50" in captured.out  # Total ARS amount
        assert "USD: 10.25" in captured.out
        assert "✅ YES" in captured.out

    def test_print_processing_summary_with_mismatch(self, capsys):
        """Test print_processing_summary with balance mismatch"""
        # Create sample DataFrame
        data = [
            {
                "Date": "2022-12-01",
                "Description": "Test Transaction",
                "Currency": "ARS",
                "Amount": 1000.50,
            },
        ]
        df = pd.DataFrame(data)

        reported_balance = {"ars": 1000.50, "usd": 10.25}
        computed_balance = {"ars": 999.50, "usd": 9.25}  # Mismatched

        print_processing_summary(
            "test_file.pdf", df, reported_balance, computed_balance, "output.xlsx"
        )

        captured = capsys.readouterr()
        assert "❌ NO" in captured.out
        assert "Reported ARS: 1,000.50" in captured.out
        assert "Computed ARS: 999.50" in captured.out

    def test_print_processing_summary_large_numbers(self, capsys):
        """Test print_processing_summary with large numbers"""
        # Create sample DataFrame with large amounts
        data = [
            {
                "Date": "2022-12-01",
                "Description": "Large Transaction",
                "Currency": "ARS",
                "Amount": 1000000.99,
            },
        ]
        df = pd.DataFrame(data)

        reported_balance = {"ars": 1000000.99, "usd": 0.0}
        computed_balance = {"ars": 1000000.99, "usd": 0.0}

        print_processing_summary(
            "large_file.pdf",
            df,
            reported_balance,
            computed_balance,
            "large_output.xlsx",
        )

        captured = capsys.readouterr()
        assert "ARS: 1,000,000.99" in captured.out
        assert "USD: 0.00" in captured.out
