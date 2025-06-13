from parse_visa_statement import parse_visa_pdf
import tempfile
import os
from unittest.mock import patch, MagicMock
import pandas as pd


class TestErrorHandlingPaths:
    """Unit tests to cover error handling paths for 100% coverage"""

    def test_tax_parsing_with_invalid_amounts(self):
        """Test tax parsing with amounts that cause ValueError"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 IMPUESTO DE SELLOS 1.500,75
        02.12.22 DB.IMPUESTO PAIS invalid-number
        03.12.22 IIBB PERCEP 2.000,50
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

                # Should parse valid entries and skip invalid ones
                assert len(result) >= 2  # At least the valid tax entries
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_payment_parsing_with_invalid_amounts(self):
        """Test payment parsing with amounts that cause ValueError"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 SU PAGO EN PESOS 1.500,75-
        02.12.22 SU PAGO EN PESOS invalid-amount
        03.12.22 SU PAGO EN USD 25,50-
        04.12.22 SU PAGO EN USD also-invalid
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

                # Should parse valid entries and skip invalid ones
                assert len(result) >= 2  # At least the valid payment entries
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_adjustment_parsing_with_invalid_amounts(self):
        """Test adjustment parsing with amounts that cause ValueError"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 AJUSTE P/DESCNTO. EN COMERCIO 1.200,00-
        02.12.22 AJUSTE P/DESCNTO. EN COMERCIO invalid-format
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

                # Should parse valid entries and skip invalid ones
                assert len(result) >= 1  # At least the valid adjustment entry
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_bonification_parsing_with_invalid_amounts(self):
        """Test bonification parsing with amounts that cause ValueError"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 BONIF. CONSUMO CABIFY25169EPTMFAA 1.190,07-
        02.12.22 BONIF. CONSUMO INVALID invalid-format
        03.12.22 OFF Promo Visa Subtes 304,15-
        04.12.22 OFF Promo Invalid also-invalid
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

                # Should parse valid entries and skip invalid ones
                assert len(result) >= 2  # At least the valid bonification entries
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_regular_transaction_fallback_paths(self):
        """Test regular transaction parsing fallback with European amounts"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 ABC123 MERCHANT NAME 1.500,75
        02.12.22 XYZ456 ANOTHER MERCHANT 2.345.678,90
        03.12.22 DEF789 FALLBACK MERCHANT invalid-amount
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

                # Should parse valid transactions and handle European format
                assert len(result) >= 2  # At least the valid transactions
                # Verify European number conversion worked
                amounts = result["Amount"].tolist()
                assert 1500.75 in amounts
                assert 2345678.90 in amounts
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_last_resort_number_parsing(self):
        """Test last resort number parsing with various edge cases"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 ABC123 VALID TRANSACTION 1500,75
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

                # Should parse valid transaction
                assert len(result) >= 1  # At least one valid transaction
                amounts = result["Amount"].tolist()
                assert all(amount > 0 for amount in amounts)  # Only positive amounts
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
