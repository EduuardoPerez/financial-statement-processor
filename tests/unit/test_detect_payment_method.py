import pdfplumber
import pytest

from parse_visa_statement import detect_payment_method


class TestDetectPaymentMethodByContent:
    """Content-based detection from PDF text."""

    @pytest.mark.parametrize(
        "content, expected",
        [
            (
                "VISA SIGNATURE\nMACRO PREMIA\nwww.macro.com.ar",
                "Macro VISA",
            ),
            (
                "BANCO MACRO S.A.\nVISA SIGNATURE",
                "Macro VISA",
            ),
            (
                "VISA\nPara consultas ingrese a www.macro.com.ar",
                "Macro VISA",
            ),
            (
                "visa signature\nmacro premia",
                "Macro VISA",
            ),
            (
                "VISA SIGNATURE\nBBVA\nwww.bbva.com.ar",
                "BBVA VISA",
            ),
            (
                "BANCO BBVA ARGENTINA S.A.\nVISA SIGNATURE",
                "BBVA VISA",
            ),
            (
                "VISA\nPara consultas ingrese a www.bbva.com.ar",
                "BBVA VISA",
            ),
            (
                "visa signature\nbbva argentina",
                "BBVA VISA",
            ),
            (
                "Mastercard Black\nBBVA\nwww.bbva.com.ar",
                "BBVA Mastercard",
            ),
            (
                "mastercard black\nbbva argentina",
                "BBVA Mastercard",
            ),
            # Mastercard precedence over VISA when both present
            (
                "BBVA\nVISA\nMASTERCARD",
                "BBVA Mastercard",
            ),
            (
                "BBVA\nVISA SIGNATURE",
                "BBVA VISA",
            ),
            # Bank precedence when both indicators are present
            (
                "VISA SIGNATURE\nMACRO PREMIA\nSome mention of BBVA in text",
                "Macro VISA",
            ),
            (
                "VISA SIGNATURE\nBBVA ARGENTINA\nSome mention of macro in text",
                "BBVA VISA",
            ),
        ],
    )
    def test_detect_from_content(self, content, expected):
        assert detect_payment_method(content) == expected

    @pytest.mark.parametrize(
        "content",
        [
            # Missing bank indicator
            "VISA SIGNATURE\nSome other bank content",
            # Missing VISA indicator
            "MACRO PREMIA\nSome other card type",
            # Empty
            "",
        ],
    )
    def test_detect_unknown_content(self, content):
        assert detect_payment_method(content) == "Unknown Payment Method"


class TestDetectPaymentMethodByFilename:
    """Filename-based detection for XLS/CSV/XLSX."""

    @pytest.mark.parametrize(
        "filename, expected",
        [
            # BBVA Account XLS
            (
                "tests/test_data/input/BBVA-Account-Detalle_mov_cuenta_07_06_2025.xls",
                "BBVA Account",
            ),
            ("BBVA-DETALLE-movimientos.xls", "BBVA Account"),
            ("bbva-account-statement.xls", "BBVA Account"),
            ("BBVA-ACCOUNT-detalle.xls", "BBVA Account"),
            ("account-bbva-detalle.xls", "BBVA Account"),
            # Macro Account XLS
            (
                "tests/test_data/input/MACRO-movimientos-de-cuenta.xls",
                "Macro Account",
            ),
            ("MACRO-MOVIMIENTOS-statement.xls", "Macro Account"),
            ("macro-movimientos-detalle.xls", "Macro Account"),
            ("MACRO-MOVIMIENTOS-de-cuenta.xls", "Macro Account"),
            ("movimientos-macro-cuenta.xls", "Macro Account"),
            # Macro Account case insensitive
            ("macro-movimientos-de-cuenta.xls", "Macro Account"),
            ("MACRO-MOVIMIENTOS-DE-CUENTA.XLS", "Macro Account"),
            ("Macro-Movimientos-De-Cuenta.xls", "Macro Account"),
            # BBVA VISA CSV
            (
                "tests/test_data/input/BBVA-Visa-Autorizaciones.csv",
                "BBVA VISA",
            ),
            (
                "tests/test_data/input/BBVA-Visa-Movimientos.csv",
                "BBVA VISA",
            ),
            ("BBVA-VISA-statements.csv", "BBVA VISA"),
            ("bbva-visa-transactions.csv", "BBVA VISA"),
            ("BBVA-VISA-auth.csv", "BBVA VISA"),
            ("visa-bbva-movimientos.csv", "BBVA VISA"),
            # Macro VISA CSV
            (
                "tests/test_data/input/MACRO-Visa-Autorizaciones.csv",
                "Macro VISA",
            ),
            (
                "tests/test_data/input/MACRO-VISA-ult-Movimientos.csv",
                "Macro VISA",
            ),
            ("MACRO-VISA-statements.csv", "Macro VISA"),
            ("macro-visa-transactions.csv", "Macro VISA"),
            ("MACRO-VISA-auth.csv", "Macro VISA"),
            ("visa-macro-movimientos.csv", "Macro VISA"),
            # CSV case-insensitive
            ("bbva-visa-autorizaciones.csv", "BBVA VISA"),
            ("BBVA-VISA-MOVIMIENTOS.CSV", "BBVA VISA"),
            ("Bbva-Visa-Statement.csv", "BBVA VISA"),
            ("macro-visa-autorizaciones.csv", "Macro VISA"),
            ("MACRO-VISA-MOVIMIENTOS.CSV", "Macro VISA"),
            ("Macro-Visa-Statement.csv", "Macro VISA"),
            # Mercadopago XLSX
            ("mercadopago.xlsx", "Mercadopago"),
            ("MERCADOPAGO.xlsx", "Mercadopago"),
            ("Mercadopago_2025.xlsx", "Mercadopago"),
            ("mercadopago-statement.xlsx", "Mercadopago"),
            ("MERCADOPAGO-transactions.xlsx", "Mercadopago"),
            ("mercadopago-account.xlsx", "Mercadopago"),
            ("MERCADOPAGO.XLSX", "Mercadopago"),
            ("MercadoPago.xlsx", "Mercadopago"),
        ],
    )
    def test_detect_from_filename(self, filename, expected):
        assert detect_payment_method(file_path=filename) == expected

    @pytest.mark.parametrize(
        "filename",
        [
            # Unknown XLS
            "santander-account.xls",
            "unknown-bank-statement.xls",
            "other-financial-data.xls",
            # Unknown CSV
            "santander-visa.csv",
            "unknown-bank-statement.csv",
            "other-financial-data.csv",
            "visa-only.csv",  # missing bank identifier
            "bbva-only.csv",  # missing card type identifier
            # Unknown XLSX
            "santander-account.xlsx",
            "unknown-bank-statement.xlsx",
            "other-financial-data.xlsx",
            "random-file.xlsx",
            "other-bank.xlsx",
        ],
    )
    def test_detect_unknown_filename(self, filename):
        assert detect_payment_method(file_path=filename) == "Unknown Payment Method"


class TestDetectPaymentMethodPrecedence:
    """Interaction between filename and content detection."""

    def test_xls_filename_takes_precedence_over_content(self):
        """XLS filename detection trumps content detection."""
        result = detect_payment_method(
            content_or_path="BBVA-DETALLE-account.xls",
            full_text="MACRO PREMIA VISA",
        )
        assert result == "BBVA Account"

    def test_non_xls_file_uses_content(self):
        """Non-XLS files fall back to content detection."""
        result = detect_payment_method(
            file_path="MACRO-statement.pdf",
            full_text="MACRO PREMIA VISA",
        )
        assert result == "Macro VISA"


class TestDetectPaymentMethodWithRealFiles:
    """Verify detection against the actual fixture files checked into the repo."""

    @pytest.mark.parametrize(
        "pdf_path, expected",
        [
            (
                "tests/test_data/input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf",
                "Macro VISA",
            ),
            (
                "tests/test_data/input/BBVA-VISA-resumen_cuenta_visa_May_2025.pdf",
                "BBVA VISA",
            ),
            (
                "tests/test_data/input/BBVA-Mastercard-2025-04.pdf",
                "BBVA Mastercard",
            ),
        ],
    )
    def test_detect_from_real_pdf_content(self, pdf_path, expected):
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "".join(
                (page.extract_text() or "") + "\n" for page in pdf.pages
            )
        assert detect_payment_method(full_text) == expected

    @pytest.mark.parametrize(
        "path, expected",
        [
            (
                "tests/test_data/input/MACRO-movimientos-de-cuenta.xls",
                "Macro Account",
            ),
            (
                "tests/test_data/input/BBVA-Account-Detalle_mov_cuenta_07_06_2025.xls",
                "BBVA Account",
            ),
            (
                "tests/test_data/input/BBVA-Visa-Autorizaciones.csv",
                "BBVA VISA",
            ),
            (
                "tests/test_data/input/BBVA-Visa-Movimientos.csv",
                "BBVA VISA",
            ),
            (
                "tests/test_data/input/MACRO-Visa-Autorizaciones.csv",
                "Macro VISA",
            ),
            (
                "tests/test_data/input/MACRO-VISA-ult-Movimientos.csv",
                "Macro VISA",
            ),
            ("tests/test_data/input/mercadopago.xlsx", "Mercadopago"),
        ],
    )
    def test_detect_from_real_filename(self, path, expected):
        assert detect_payment_method(file_path=path) == expected
