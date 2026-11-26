"""Source evidence and row accounting at parser boundaries."""

import hashlib
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd

from domain.builders import TransactionBuilder
from domain.models import PaymentMethod
from domain.utils import AmountParser, DateConverter
from infrastructure.parsers.csv_parser import CSVStatementParser
from infrastructure.parsers.pdf_parser import PDFStatementParser
from infrastructure.parsers.xls_parser import XLSStatementParser
from infrastructure.parsers.xlsx_parser import XLSXStatementParser


class Detector:
    def detect_from_filename(self, path: Path) -> PaymentMethod:
        return PaymentMethod.BBVA_VISA


def builder() -> TransactionBuilder:
    return TransactionBuilder(DateConverter(), AmountParser())


def test_csv_preserves_original_values_and_accounts_for_invalid_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "synthetic.csv"
    path.write_text(
        "Fecha;Establecimiento;Moneda;Importe;SOURCE_ID\n"
        "01/02/2025;Shop;Pesos;1,234.567890123456;0007\n"
        "bad;Other;Pesos;4.00;0008\n",
        encoding="utf-8",
    )
    parser = CSVStatementParser(Detector(), builder())

    statement = parser.parse(path)

    assert len(statement.transactions) == 1
    transaction = statement.transactions[0]
    assert transaction.date == date(2025, 2, 1)
    assert transaction.amount == Decimal("1234.567890123456")
    assert transaction.provenance is not None
    assert (
        transaction.provenance.file_sha256
        == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert transaction.provenance.locator == "row:2"
    assert transaction.provenance.raw_date == "01/02/2025"
    assert transaction.provenance.raw_amount == "1,234.567890123456"
    assert transaction.provenance.raw_currency == "Pesos"
    assert transaction.provenance.native_ids == {"SOURCE_ID": "0007"}
    assert transaction.provenance.source_identity_key is None
    assert statement.extraction is not None
    assert (
        statement.extraction.rows_read,
        statement.extraction.rows_emitted,
        statement.extraction.rows_discarded,
    ) == (2, 1, 1)
    assert statement.extraction.diagnostics[0].locator == "row:3"
    assert statement.extraction.diagnostics[0].reason


def test_mastercard_header_dates_define_cycle_without_discarded_rows() -> None:
    class MastercardDetector:
        def detect_from_content(self, content: str) -> PaymentMethod:
            return PaymentMethod.BBVA_MASTERCARD

    parser = PDFStatementParser(MastercardDetector(), builder())
    content = (
        "CIERRE ACTUAL VENCIMIENTO ACTUAL SALDO ACTUAL $\n"
        "30-Jun-26 10-Jul-26 1.000,00 0,00 100,00\n"
        "CIERRE ANTERIOR VENCIMIENTO ANTERIOR PRÓXIMO CIERRE PRÓXIMO VENCIMIENTO\n"
        "Otros períodos\n"
        "31-May-26 10-Jun-26 31-Jul-26 10-Ago-26\n"
        "05-Apr-26 123456* STORE Cuota 03/06 25,00\n"
    )
    from domain.models import ExtractionResult

    report = ExtractionResult("a" * 64)
    transactions = parser._parse_transactions(
        content, PaymentMethod.BBVA_MASTERCARD, report
    )
    assert len(transactions) == 1
    assert (report.rows_read, report.rows_emitted, report.rows_discarded) == (1, 1, 0)
    assert parser.statement_cycle(content) == (date(2026, 6, 1), date(2026, 6, 30))
    assert transactions[0].date == date(2026, 4, 5)


def test_mastercard_cycle_requires_close_labels() -> None:
    parser = PDFStatementParser(Detector(), builder())
    content = (
        "30-Jun-26 10-Jul-26 1.000,00 0,00 100,00\n"
        "31-May-26 10-Jun-26 31-Jul-26 10-Ago-26\n"
    )
    assert parser.statement_cycle(content) is None
    from domain.models import ExtractionResult

    report = ExtractionResult("a" * 64)
    parser._parse_transactions(content, PaymentMethod.BBVA_MASTERCARD, report)
    assert report.rows_discarded == 2


def test_csv_blank_record_is_excluded_from_logical_locator(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.csv"
    path.write_text(
        "Fecha;Establecimiento;Moneda;Importe\n"
        "01/02/2025;Shop;Pesos;1.00\n"
        "\n"
        "bad;Other;Pesos;4.00\n",
        encoding="utf-8",
    )

    statement = CSVStatementParser(Detector(), builder()).parse(path)

    assert statement.extraction.rows_read == 2
    assert statement.extraction.diagnostics[0].locator == "row:3"


def test_csv_keeps_voucher_and_both_source_dates(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.csv"
    path.write_text(
        "Fecha;Fecha Origen;Establecimiento;Numero Comprobante;Moneda;Importe\n"
        "02/02/2025;01/02/2025;Shop;0009;Pesos;3.00\n",
        encoding="utf-8",
    )

    transaction = CSVStatementParser(Detector(), builder()).parse(path).transactions[0]

    assert transaction.provenance.raw_dates == {
        "Fecha": "02/02/2025",
        "Fecha Origen": "01/02/2025",
    }
    assert transaction.provenance.references == {"Numero Comprobante": "0009"}


def test_csv_raw_fields_keep_source_whitespace(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.csv"
    path.write_text(
        "Fecha;Establecimiento;Moneda;Importe\n 01/02/2025 ; Shop ; Pesos ; 3.00 \n",
        encoding="utf-8",
    )

    transaction = CSVStatementParser(Detector(), builder()).parse(path).transactions[0]

    assert transaction.provenance.raw_date == " 01/02/2025 "
    assert transaction.provenance.raw_description == " Shop "
    assert transaction.provenance.raw_amount == " 3.00 "
    assert transaction.provenance.raw_currency == " Pesos "


def test_csv_keeps_literal_na_description(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.csv"
    path.write_text(
        "Fecha;Establecimiento;Moneda;Importe\n01/02/2025;NA;Pesos;3.00\n",
        encoding="utf-8",
    )

    statement = CSVStatementParser(Detector(), builder()).parse(path)

    assert statement.transactions[0].description == "NA"
    assert statement.transactions[0].provenance.raw_description == "NA"


def test_csv_detects_input_replacement_during_extraction(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.csv"
    header = "Fecha;Establecimiento;Moneda;Importe\n"
    path.write_text(header + "01/02/2025;Shop;Pesos;3.00\n", encoding="utf-8")
    parser = CSVStatementParser(Detector(), builder())
    original_load = parser._load_csv_data

    def changing_load(file_path: Path) -> pd.DataFrame:
        frame = original_load(file_path)
        file_path.write_text(header + "01/02/2025;Other;Pesos;3.00\n", encoding="utf-8")
        return frame

    parser._load_csv_data = changing_load

    import pytest

    with pytest.raises(OSError, match="changed during extraction"):
        parser.parse(path)


def test_xlsx_retains_repeated_observations_and_installment_reference(
    tmp_path: Path,
) -> None:
    rows = pd.DataFrame(
        [
            {
                "Fecha y hora": "07/07/25",
                "Movimientos": "Charge",
                "Cuota": "01/02",
                "Monto": "USD 35,00",
            }
        ]
    )
    paths = [tmp_path / "BBVA-Mastercard-A.xlsx", tmp_path / "BBVA-Mastercard-B.xlsx"]
    rows.to_excel(paths[0], index=False, startrow=2)
    pd.concat(
        [
            rows,
            pd.DataFrame(
                [
                    {
                        "Fecha y hora": "08/07/25",
                        "Movimientos": "Other charge",
                        "Cuota": "02/02",
                        "Monto": "USD 35,00",
                    }
                ]
            ),
        ],
        ignore_index=True,
    ).to_excel(paths[1], index=False, startrow=2)

    class MastercardDetector:
        def detect_from_filename(self, path: Path) -> PaymentMethod:
            return PaymentMethod.BBVA_MASTERCARD

    parser = XLSXStatementParser(MastercardDetector(), builder())
    transactions = [parser.parse(path).transactions[0] for path in paths]

    assert len(transactions) == 2
    assert all(t.provenance is not None for t in transactions)
    assert transactions[0].provenance.locator == "row:4"
    assert transactions[0].provenance.raw_amount == "USD 35,00"
    assert transactions[0].provenance.raw_currency == "USD"
    assert transactions[0].provenance.references == {"Cuota": "01/02"}
    assert transactions[0].provenance.source_identity_key is None
    assert (
        transactions[0].provenance.file_sha256 != transactions[1].provenance.file_sha256
    )


def test_xls_reports_bad_data_row_and_keeps_numeric_precision(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.xls"
    path.write_bytes(b"synthetic test input")
    frame = pd.DataFrame(
        [
            ["Title", None, None, None],
            ["Header", None, None, None],
            ["01/02/2025", "Transfer", None, "1.234,5600"],
            ["invalid", "Transfer", None, "5,00"],
        ]
    )

    class AccountDetector:
        def detect_from_filename(self, path: Path) -> PaymentMethod:
            return PaymentMethod.BBVA_ACCOUNT

    parser = XLSStatementParser(AccountDetector(), builder())
    parser._load_excel_data = lambda _: frame
    statement = parser.parse(path)

    assert statement.transactions[0].amount == Decimal("1234.5600")
    assert statement.transactions[0].provenance.raw_amount == "1.234,5600"
    assert statement.transactions[0].provenance.locator == "row:4"
    assert (
        statement.extraction.rows_read,
        statement.extraction.rows_emitted,
        statement.extraction.rows_discarded,
    ) == (2, 1, 1)
    assert statement.extraction.diagnostics[0].locator == "row:5"


def test_mercadopago_xlsx_keeps_text_identifier_leading_zero(tmp_path: Path) -> None:
    path = tmp_path / "mercadopago.xlsx"
    pd.DataFrame(
        [
            {
                "Fecha de Pago": "2025-02-01T17:45:36Z",
                "Tipo de Operación": "Payment",
                "Importe": "12.3400",
                "Número de Movimiento": "0007",
            }
        ]
    ).to_excel(path, index=False)

    class MercadoPagoDetector:
        def detect_from_filename(self, path: Path) -> PaymentMethod:
            return PaymentMethod.MERCADOPAGO

    statement = XLSXStatementParser(MercadoPagoDetector(), builder()).parse(path)

    assert statement.transactions[0].provenance.native_ids == {
        "Número de Movimiento": "0007"
    }
    assert statement.transactions[0].provenance.raw_amount == "12.3400"


def test_pdf_accounts_for_date_led_line_without_transaction(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.pdf"
    path.write_bytes(b"synthetic test input")

    class PdfDetector:
        def detect_from_content(self, text: str) -> PaymentMethod:
            return PaymentMethod.BBVA_VISA

    parser = PDFStatementParser(PdfDetector(), builder())
    parser._extract_text = lambda _: (
        "Page heading\n05.06.25 IMPUESTO DE SELLOS 1.234,50\n06.06.25 UNKNOWN LINE\n"
    )
    statement = parser.parse(path)

    assert len(statement.transactions) == 1
    assert statement.transactions[0].provenance.raw_date == "05.06.25"
    assert statement.transactions[0].provenance.raw_amount == "1.234,50"
    assert statement.transactions[0].provenance.locator == "line:2"
    assert (
        statement.extraction.rows_read,
        statement.extraction.rows_emitted,
        statement.extraction.rows_discarded,
    ) == (2, 1, 1)
    assert statement.extraction.diagnostics[0].locator == "line:3"


def test_pdf_keeps_reference_installment_and_amount_token(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.pdf"
    path.write_bytes(b"synthetic test input")

    class PdfDetector:
        def detect_from_content(self, text: str) -> PaymentMethod:
            return PaymentMethod.BBVA_VISA

    parser = PDFStatementParser(PdfDetector(), builder())
    parser._extract_text = lambda _: (
        "05.06.25 AB123* ON FIT Cuota 06/06 32.990,00\n"
        "30.04.26 BONIF. PROMO BILLETERA 10.590,00- _"
    )

    statement = parser.parse(path)

    assert statement.transactions[0].provenance.references == {
        "source_reference": "AB123*",
        "Cuota": "06/06",
    }
    assert statement.transactions[0].provenance.raw_amount == "32.990,00"
    assert statement.transactions[1].provenance.raw_amount == "10.590,00-"
