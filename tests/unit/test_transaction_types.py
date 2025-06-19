import os
import tempfile
from unittest.mock import MagicMock, patch

from parse_visa_statement import parse_visa_pdf


class TestTransactionTypes:
    """Test parsing of different transaction types"""

    def test_tax_transaction_parsing(self):
        """Test parsing of various tax transactions"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 IMPUESTO DE SELLOS 150,75
        02.12.22 DB.IMPUESTO PAIS 250,50
        03.12.22 IIBB PERCEP 75,25
        04.12.22 IVA RG 100,00
        05.12.22 DB.RG 50,30
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

                # Should parse all tax transactions
                assert len(result) == 5
                # All should be positive amounts (taxes are charges)
                assert all(amount > 0 for amount in result["Amount"])
                # All should be ARS currency
                assert all(currency == "ARS" for currency in result["Currency"])
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_payment_transaction_parsing(self):
        """Test parsing of payment transactions in different currencies"""
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
                # All payments should be negative
                assert all(amount < 0 for amount in result["Amount"])

                # Check ARS payment
                ars_payment = result[result["Currency"] == "ARS"].iloc[0]
                assert ars_payment["Description"] == "SU PAGO EN PESOS"
                assert abs(ars_payment["Amount"] - (-1500.75)) < 0.01

                # Check USD payment
                usd_payment = result[result["Currency"] == "USD"].iloc[0]
                assert usd_payment["Description"] == "SU PAGO EN USD"
                assert abs(usd_payment["Amount"] - (-25.50)) < 0.01
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_adjustment_transaction_parsing(self):
        """Test parsing of adjustment transactions"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 AJUSTE P/DESCNTO. EN COMERCIO 1200,00-
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
                assert result.iloc[0]["Description"] == "AJUSTE P/DESCNTO. EN COMERCIO"
                assert result.iloc[0]["Currency"] == "ARS"
                assert result.iloc[0]["Amount"] == -1200.00  # Negative for adjustment
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_bonification_transaction_parsing(self):
        """Test parsing of BBVA bonification transactions"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 BONIF. CONSUMO CABIFY25169EPTMFAA 1190,07-
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
                assert (
                    "BONIF. CONSUMO CABIFY25169EPTMFAA" in result.iloc[0]["Description"]
                )
                assert result.iloc[0]["Currency"] == "ARS"
                assert result.iloc[0]["Amount"] == -1190.07  # Negative for bonification
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_promo_transaction_parsing(self):
        """Test parsing of promotional discount transactions"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 OFF Promo Visa Subtes 304,15-
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
                assert "OFF Promo Visa Subtes" in result.iloc[0]["Description"]
                assert result.iloc[0]["Currency"] == "ARS"
                assert (
                    result.iloc[0]["Amount"] == -304.15
                )  # Negative for promo discount
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_regular_transaction_parsing_ars(self):
        """Test parsing of regular ARS purchase transactions"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 ABC123 MERCHANT NAME PURCHASE 1500,75
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
                assert "ABC123 MERCHANT NAME PURCHASE" in result.iloc[0]["Description"]
                assert result.iloc[0]["Currency"] == "ARS"
                # Parser extracts the last number as amount
                assert result.iloc[0]["Amount"] > 0  # Positive for purchases
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_regular_transaction_parsing_usd(self):
        """Test parsing of regular USD purchase transactions"""
        pdf_content = """
        SALDO ACTUAL $ 1000,00 U$S 0,00
        01.12.22 XYZ456 AMAZON PURCHASE USD 25,50
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
                assert (
                    "XYZ456 AMAZON PURCHASE USD 25,50" in result.iloc[0]["Description"]
                )
                assert result.iloc[0]["Currency"] == "USD"
                assert result.iloc[0]["Amount"] == 25.50  # Positive for purchases
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
