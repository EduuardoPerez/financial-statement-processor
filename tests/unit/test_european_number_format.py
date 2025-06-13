from parse_visa_statement import parse_visa_pdf
import tempfile
import os
from unittest.mock import patch, MagicMock


class TestEuropeanNumberFormat:
    """Test European number format parsing (1.234,56 format)"""

    def test_european_format_with_thousands_separator(self):
        """Test parsing of amounts with both dots and commas (1.234,56)"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 ABC123 MERCHANT NAME 1.234.567,89
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            with patch("pdfplumber.open") as mock_pdf:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = pdf_content
                mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

                with patch("os.makedirs"):
                    with patch("pandas.DataFrame.to_excel"):
                        result = parse_visa_pdf(temp_path, "test_output.xlsx")

                # Should parse European format correctly
                assert len(result) == 1
                assert abs(result.iloc[0]["Amount"] - 1234567.89) < 0.01
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_comma_only_amounts_in_tax_parsing(self):
        """Test tax parsing with comma-only amounts (no dots)"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 IMPUESTO DE SELLOS 1500,75
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            with patch("pdfplumber.open") as mock_pdf:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = pdf_content
                mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

                with patch("os.makedirs"):
                    with patch("pandas.DataFrame.to_excel"):
                        result = parse_visa_pdf(temp_path, "test_output.xlsx")

                assert len(result) == 1
                assert abs(result.iloc[0]["Amount"] - 1500.75) < 0.01
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_comma_only_amounts_in_payment_parsing(self):
        """Test payment parsing with comma-only amounts"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 SU PAGO EN PESOS 1500,75-
        02.12.22 SU PAGO EN USD 25,50-
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            with patch("pdfplumber.open") as mock_pdf:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = pdf_content
                mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

                with patch("os.makedirs"):
                    with patch("pandas.DataFrame.to_excel"):
                        result = parse_visa_pdf(temp_path, "test_output.xlsx")

                assert len(result) == 2
                # First payment (ARS)
                ars_payment = result[result["Currency"] == "ARS"].iloc[0]
                assert abs(ars_payment["Amount"] - (-1500.75)) < 0.01
                # Second payment (USD)
                usd_payment = result[result["Currency"] == "USD"].iloc[0]
                assert abs(usd_payment["Amount"] - (-25.50)) < 0.01
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_fallback_european_format_parsing(self):
        """Test fallback parsing for European format in regular transactions"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 ABC123 MERCHANT with 1.500,75 fallback
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            with patch("pdfplumber.open") as mock_pdf:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = pdf_content
                mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

                with patch("os.makedirs"):
                    with patch("pandas.DataFrame.to_excel"):
                        result = parse_visa_pdf(temp_path, "test_output.xlsx")

                # Should parse with fallback European format logic
                assert len(result) == 1
                amounts = result["Amount"].tolist()
                assert any(abs(amount - 1500.75) < 0.01 for amount in amounts)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_bbva_mastercard_european_format(self):
        """Test European format parsing for BBVA Mastercard transactions"""
        pdf_content = """
        04-Abr-25 29-May-25 06-Jun-
        15-Mar-25 SALDO ACTUAL $ 185.170,00 SALDO ACTUAL U$S 0,00
        15-Mar-25 SU PAGO EN PESOS 1500,75-
        16-Mar-25 MERCHANT TRANSACTION REF123 1500,75
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            with patch("pdfplumber.open") as mock_pdf:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = pdf_content
                mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

                with patch("os.makedirs"):
                    with patch("pandas.DataFrame.to_excel"):
                        result = parse_visa_pdf(temp_path, "test_output.xlsx")

                # Should parse payment and regular transaction(s)
                assert len(result) >= 2
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
