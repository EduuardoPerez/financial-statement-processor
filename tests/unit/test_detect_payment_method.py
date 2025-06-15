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

    def test_detect_bbva_account_xls_filename(self):
        """Test detection of BBVA Account from XLS filename"""
        test_filenames = [
            "tests/test_data/input/BBVA-Account-Detalle_mov_cuenta_07_06_2025.xls",
            "BBVA-DETALLE-movimientos.xls",
            "bbva-account-statement.xls",
            "BBVA-ACCOUNT-detalle.xls",
            "account-bbva-detalle.xls",
        ]

        for filename in test_filenames:
            result = detect_payment_method(file_path=filename)
            assert (
                result == "BBVA Account"
            ), f"Should detect BBVA Account from {filename}"

    def test_detect_macro_account_xls_filename(self):
        """Test detection of Macro Account from XLS filename"""
        test_filenames = [
            "tests/test_data/input/MACRO-movimientos-de-cuenta.xls",
            "MACRO-MOVIMIENTOS-statement.xls",
            "macro-movimientos-detalle.xls",
            "MACRO-MOVIMIENTOS-de-cuenta.xls",
            "movimientos-macro-cuenta.xls",
        ]

        for filename in test_filenames:
            result = detect_payment_method(file_path=filename)
            assert (
                result == "Macro Account"
            ), f"Should detect Macro Account from {filename}"

    def test_detect_macro_account_case_insensitive(self):
        """Test that Macro Account detection is case insensitive"""
        test_filenames = [
            "macro-movimientos-de-cuenta.xls",
            "MACRO-MOVIMIENTOS-DE-CUENTA.XLS",
            "Macro-Movimientos-De-Cuenta.xls",
        ]

        for filename in test_filenames:
            result = detect_payment_method(file_path=filename)
            assert (
                result == "Macro Account"
            ), f"Should detect Macro Account from {filename}"

    def test_detect_xls_vs_pdf_precedence(self):
        """Test that XLS filename detection takes precedence over content detection"""
        # Test with BBVA Account XLS file but Macro content (shouldn't happen in practice)
        bbva_filename = "BBVA-DETALLE-account.xls"
        macro_content = "MACRO PREMIA VISA"

        result = detect_payment_method(
            content_or_path=bbva_filename, full_text=macro_content
        )
        assert result == "BBVA Account", "XLS filename detection should take precedence"

    def test_detect_non_xls_files_use_content(self):
        """Test that non-XLS files fall back to content detection"""
        pdf_filename = "MACRO-statement.pdf"
        macro_content = "MACRO PREMIA VISA"

        result = detect_payment_method(file_path=pdf_filename, full_text=macro_content)
        assert result == "Macro VISA", "Should use content detection for non-XLS files"

    def test_detect_unknown_xls_filename(self):
        """Test that unknown XLS filenames return Unknown Payment Method"""
        unknown_filenames = [
            "santander-account.xls",
            "unknown-bank-statement.xls",
            "other-financial-data.xls",
        ]

        for filename in unknown_filenames:
            result = detect_payment_method(file_path=filename)
            assert (
                result == "Unknown Payment Method"
            ), f"Should return Unknown for {filename}"

    def test_detect_with_actual_macro_account_xls_file(self):
        """Test with actual Macro Account XLS file to ensure correct detection"""
        xls_path = "tests/test_data/input/MACRO-movimientos-de-cuenta.xls"

        result = detect_payment_method(file_path=xls_path)
        assert result == "Macro Account"

    def test_detect_with_actual_bbva_account_xls_file(self):
        """Test with actual BBVA Account XLS file to ensure correct detection"""
        xls_path = (
            "tests/test_data/input/BBVA-Account-Detalle_mov_cuenta_07_06_2025.xls"
        )

        result = detect_payment_method(file_path=xls_path)
        assert result == "BBVA Account"

    def test_detect_bbva_visa_csv_filename(self):
        """Test detection of BBVA VISA from CSV filename"""
        test_filenames = [
            "tests/test_data/input/BBVA-Visa-Autorizaciones.csv",
            "tests/test_data/input/BBVA-Visa-Movimientos.csv",
            "BBVA-VISA-statements.csv",
            "bbva-visa-transactions.csv",
            "BBVA-VISA-auth.csv",
            "visa-bbva-movimientos.csv",
        ]

        for filename in test_filenames:
            result = detect_payment_method(file_path=filename)
            assert result == "BBVA VISA", f"Should detect BBVA VISA from {filename}"

    def test_detect_macro_visa_csv_filename(self):
        """Test detection of Macro VISA from CSV filename"""
        test_filenames = [
            "tests/test_data/input/MACRO-Visa-Autorizaciones.csv",
            "tests/test_data/input/MACRO-VISA-ult-Movimientos.csv",
            "MACRO-VISA-statements.csv",
            "macro-visa-transactions.csv",
            "MACRO-VISA-auth.csv",
            "visa-macro-movimientos.csv",
        ]

        for filename in test_filenames:
            result = detect_payment_method(file_path=filename)
            assert result == "Macro VISA", f"Should detect Macro VISA from {filename}"

    def test_detect_csv_case_insensitive(self):
        """Test that CSV detection is case insensitive"""
        test_cases = [
            ("bbva-visa-autorizaciones.csv", "BBVA VISA"),
            ("BBVA-VISA-MOVIMIENTOS.CSV", "BBVA VISA"),
            ("Bbva-Visa-Statement.csv", "BBVA VISA"),
            ("macro-visa-autorizaciones.csv", "Macro VISA"),
            ("MACRO-VISA-MOVIMIENTOS.CSV", "Macro VISA"),
            ("Macro-Visa-Statement.csv", "Macro VISA"),
        ]

        for filename, expected in test_cases:
            result = detect_payment_method(file_path=filename)
            assert result == expected, f"Failed for {filename}, expected {expected}"

    def test_detect_unknown_csv_filename(self):
        """Test that unknown CSV filenames return Unknown Payment Method"""
        unknown_filenames = [
            "santander-visa.csv",
            "unknown-bank-statement.csv",
            "other-financial-data.csv",
            "visa-only.csv",  # Missing bank identifier
            "bbva-only.csv",  # Missing card type identifier
        ]

        for filename in unknown_filenames:
            result = detect_payment_method(file_path=filename)
            assert (
                result == "Unknown Payment Method"
            ), f"Should return Unknown for {filename}"

    def test_detect_with_actual_bbva_visa_csv_files(self):
        """Test with actual BBVA VISA CSV files to ensure correct detection"""
        csv_files = [
            "tests/test_data/input/BBVA-Visa-Autorizaciones.csv",
            "tests/test_data/input/BBVA-Visa-Movimientos.csv",
        ]

        for csv_path in csv_files:
            result = detect_payment_method(file_path=csv_path)
            assert result == "BBVA VISA", f"Failed to detect BBVA VISA from {csv_path}"

    def test_detect_with_actual_macro_visa_csv_files(self):
        """Test with actual Macro VISA CSV files to ensure correct detection"""
        csv_files = [
            "tests/test_data/input/MACRO-Visa-Autorizaciones.csv",
            "tests/test_data/input/MACRO-VISA-ult-Movimientos.csv",
        ]

        for csv_path in csv_files:
            result = detect_payment_method(file_path=csv_path)
            assert (
                result == "Macro VISA"
            ), f"Failed to detect Macro VISA from {csv_path}"
