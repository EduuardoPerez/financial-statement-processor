import pdfplumber
from parse_visa_statement import detect_payment_method


class TestDetectPaymentMethod:
    """Unit tests for the detect_payment_method function"""

    def test_detect_macro_visa(self):
        """Test detection of Macro VISA from typical content"""
        content = """
        VISA SIGNATURE
        MACRO PREMIA
        www.macro.com.ar
        """
        result = detect_payment_method(content)
        assert result == "Macro VISA"

    def test_detect_with_banco_macro(self):
        """Test detection with BANCO MACRO text"""
        content = """
        BANCO MACRO S.A.
        VISA SIGNATURE
        """
        result = detect_payment_method(content)
        assert result == "Macro VISA"

    def test_detect_with_macro_website(self):
        """Test detection with macro website reference"""
        content = """
        VISA
        Para consultas ingrese a www.macro.com.ar
        """
        result = detect_payment_method(content)
        assert result == "Macro VISA"

    def test_detect_macro_case_insensitive(self):
        """Test that MACRO detection is case insensitive"""
        content = """
        visa signature
        macro premia
        """
        result = detect_payment_method(content)
        assert result == "Macro VISA"

    def test_detect_bbva_visa(self):
        """Test detection of BBVA VISA from typical content"""
        content = """
        VISA SIGNATURE
        BBVA
        www.bbva.com.ar
        """
        result = detect_payment_method(content)
        assert result == "BBVA VISA"

    def test_detect_with_banco_bbva(self):
        """Test detection with BANCO BBVA text"""
        content = """
        BANCO BBVA ARGENTINA S.A.
        VISA SIGNATURE
        """
        result = detect_payment_method(content)
        assert result == "BBVA VISA"

    def test_detect_with_bbva_website(self):
        """Test detection with BBVA website reference"""
        content = """
        VISA
        Para consultas ingrese a www.bbva.com.ar
        """
        result = detect_payment_method(content)
        assert result == "BBVA VISA"

    def test_detect_bbva_case_insensitive(self):
        """Test that BBVA detection is case insensitive"""
        content = """
        visa signature
        bbva argentina
        """
        result = detect_payment_method(content)
        assert result == "BBVA VISA"

    def test_detect_bbva_mastercard(self):
        """Test detection of BBVA Mastercard from typical content"""
        content = """
        Mastercard Black
        BBVA
        www.bbva.com.ar
        """
        result = detect_payment_method(content)
        assert result == "BBVA Mastercard"

    def test_detect_bbva_mastercard_case_insensitive(self):
        """Test that BBVA Mastercard detection is case insensitive"""
        content = """
        mastercard black
        bbva argentina
        """
        result = detect_payment_method(content)
        assert result == "BBVA Mastercard"

    def test_detect_bbva_mastercard_vs_visa_precedence(self):
        """Test that Mastercard takes precedence over VISA when both are present"""
        content = """
        BBVA
        VISA
        MASTERCARD
        """
        result = detect_payment_method(content)
        assert result == "BBVA Mastercard"

    def test_detect_bbva_visa_vs_mastercard_precedence(self):
        """Test that when only VISA is present with BBVA, it detects BBVA VISA"""
        content = """
        BBVA
        VISA SIGNATURE
        """
        result = detect_payment_method(content)
        assert result == "BBVA VISA"

    def test_detect_missing_bank_indicator(self):
        """Test when bank indicator is missing"""
        content = """
        VISA SIGNATURE
        Some other bank content
        """
        result = detect_payment_method(content)
        assert result == "Unknown Payment Method"

    def test_detect_missing_visa_indicator(self):
        """Test when VISA indicator is missing"""
        content = """
        MACRO PREMIA
        Some other card type
        """
        result = detect_payment_method(content)
        assert result == "Unknown Payment Method"

    def test_detect_empty_content(self):
        """Test with empty content"""
        result = detect_payment_method("")
        assert result == "Unknown Payment Method"

    def test_detect_with_actual_macro_pdf_content(self):
        """Test with actual MACRO PDF content to ensure it detects Macro VISA"""
        pdf_path = "tests/test_data/input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"

        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

        result = detect_payment_method(full_text)
        assert result == "Macro VISA"

    def test_detect_with_actual_bbva_pdf_content(self):
        """Test with actual BBVA PDF content to ensure it detects BBVA VISA"""
        pdf_path = "tests/test_data/input/BBVA-VISA-resumen_cuenta_visa_May_2025.pdf"

        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

        result = detect_payment_method(full_text)
        assert result == "BBVA VISA"

    def test_detect_with_actual_bbva_mastercard_pdf_content(self):
        """Test with actual BBVA Mastercard PDF content to ensure it detects BBVA Mastercard"""
        pdf_path = "tests/test_data/input/BBVA-Mastercard-2025-04.pdf"

        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

        result = detect_payment_method(full_text)
        assert result == "BBVA Mastercard"

    def test_bank_precedence_macro_over_bbva(self):
        """Test that when both bank indicators are present, detection works correctly"""
        content = """
        VISA SIGNATURE
        MACRO PREMIA
        Some mention of BBVA in text
        """
        result = detect_payment_method(content)
        assert result == "Macro VISA"

    def test_bank_precedence_bbva_over_macro(self):
        """Test that when both bank indicators are present, detection works correctly"""
        content = """
        VISA SIGNATURE
        BBVA ARGENTINA
        Some mention of macro in text
        """
        result = detect_payment_method(content)
        assert result == "BBVA VISA"
