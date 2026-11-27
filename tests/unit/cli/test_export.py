"""Structured export contract exercised through the public CLI."""

import hashlib
import json
from pathlib import Path

from click.testing import CliRunner

from cli.main import cli
from domain.builders import TransactionBuilder
from domain.models import PaymentMethod
from domain.utils import AmountParser, DateConverter
from infrastructure.parsers.pdf_parser import PDFStatementParser
from infrastructure.reconciliation_export import export_reconciliation


def export_batch(tmp_path: Path, files: list[dict]) -> tuple[dict, list[dict]]:
    declaration = tmp_path / "declaration.json"
    declaration.write_text(json.dumps({"schema_version": "1.0", "files": files}))
    output = tmp_path / "batch"
    result = CliRunner().invoke(
        cli, ["export", str(declaration), "--output-dir", str(output)]
    )
    assert result.exit_code == 0, result.output
    manifest = json.loads((output / "manifest.json").read_text())
    payload = (output / "movements.jsonl").read_bytes()
    assert manifest["movements"]["sha256"] == hashlib.sha256(payload).hexdigest()
    records = [json.loads(line) for line in payload.splitlines()]
    assert manifest["movements"]["record_count"] == len(records)
    return manifest, records


def test_export_preserves_raw_values_and_overlap(tmp_path: Path) -> None:
    rows = (
        "Fecha;Establecimiento;Moneda;Importe;SOURCE_ID\n"
        "01/02/2025;Store;Pesos;1,234.500;0007\n"
    )
    files = []
    for name in ("BBVA-Visa-Autorizaciones-a.csv", "BBVA-Visa-Autorizaciones-b.csv"):
        (tmp_path / name).write_text(rows)
        files.append({"path": name, "system": "bbva_visa", "expected_coverage": []})

    manifest, records = export_batch(tmp_path, files)

    assert manifest["complete"] is True
    assert len(records) == 2
    assert records[0]["observation_id"] == records[1]["observation_id"]
    assert records[0]["raw"]["amount"] == "1,234.500"
    assert records[0]["parsed"]["amount"] == "1234.500"
    assert records[0]["native_ids"] == {"SOURCE_ID": "0007"}
    assert records[0]["source_identity"] == {
        "status": "unconfirmed",
        "key": None,
        "basis": [],
    }
    assert all(item["status"] == "complete" for item in manifest["expected_files"])


def test_mercado_pago_csv_preserves_transaction_evidence(tmp_path: Path) -> None:
    name = "arbitrary-export.csv"
    transaction_date = "2025-04-30T23:45:00.000-03:00"
    settlement_date = "2025-05-02T09:00:00.000-03:00"
    (tmp_path / name).write_text(
        "TRANSACTION_DATE;SETTLEMENT_DATE;TRANSACTION_TYPE;TRANSACTION_CURRENCY;"
        "TRANSACTION_AMOUNT;SOURCE_ID;REAL_AMOUNT;PAYMENT_METHOD_TYPE;PURCHASE_ID;"
        "EXTERNAL_REFERENCE\n"
        f"{transaction_date};{settlement_date};SETTLEMENT;ARS;"
        "1234.56789012345678900;00042;1230.00;credit_card;;00005\n"
        f"{transaction_date};;PAYOUTS;USD;-3.50;00043;-3.50;;0008;\n"
        f"invalid;;SETTLEMENT;ARS;5.00;00044;5.00;;;\n"
    )
    manifest, records = export_batch(
        tmp_path,
        [
            {
                "path": name,
                "system": "mercado_pago_transactions",
                "expected_coverage": [],
            }
        ],
    )
    (entry,) = manifest["expected_files"]
    assert (entry["rows_read"], entry["rows_emitted"], entry["rows_discarded"]) == (
        3,
        2,
        1,
    )
    assert entry["status"] == "partial"
    assert entry["observed_coverage"] == []
    assert ("discarded_row", "row:4") in [
        (w["code"], w.get("locator")) for w in entry["warnings"]
    ]
    first, second = records
    assert first["source"]["locator"] == "row:2"
    assert first["native_ids"] == {"SOURCE_ID": "00042"}
    assert first["source_identity"] == {
        "status": "unconfirmed",
        "key": None,
        "basis": [],
    }
    assert first["raw"] == {
        "date": transaction_date,
        "dates": {
            "TRANSACTION_DATE": transaction_date,
            "SETTLEMENT_DATE": settlement_date,
        },
        "description": "SETTLEMENT",
        "currency": "ARS",
        "amount": "1234.56789012345678900",
    }
    assert first["parsed"] == {
        "amount": "1234.56789012345678900",
        "currency": "ARS",
        "description": "SETTLEMENT",
        "dates": [{"role": "transaction", "value": "2025-04-30"}],
    }
    assert first["references"] == {
        "REAL_AMOUNT": "1230.00",
        "PAYMENT_METHOD_TYPE": "credit_card",
        "EXTERNAL_REFERENCE": "00005",
        "TRANSACTION_TYPE": "SETTLEMENT",
    }
    assert second["native_ids"] == {"SOURCE_ID": "00043", "PURCHASE_ID": "0008"}
    assert second["parsed"]["amount"] == "-3.50"
    assert second["parsed"]["currency"] == "USD"
    assert second["raw"]["dates"] == {"TRANSACTION_DATE": transaction_date}


def test_missing_and_unverified_coverage_make_batch_incomplete(tmp_path: Path) -> None:
    (tmp_path / "BBVA-Visa-Autorizaciones.csv").write_text(
        "Fecha;Establecimiento;Moneda;Importe\n01/02/2025;Store;Pesos;3.00\n"
    )
    coverage = [
        {"kind": "transaction_dates", "start": "2025-02-01", "end": "2025-02-28"}
    ]
    manifest, records = export_batch(
        tmp_path,
        [
            {
                "path": "BBVA-Visa-Autorizaciones.csv",
                "system": "bbva_visa",
                "expected_coverage": coverage,
            },
            {
                "path": "missing.csv",
                "system": "bbva_visa",
                "expected_coverage": coverage,
            },
        ],
    )
    assert len(records) == 1
    assert manifest["complete"] is False
    assert [item["status"] for item in manifest["expected_files"]] == [
        "partial",
        "missing",
    ]
    assert manifest["expected_files"][0]["observed_coverage"] == []


def test_confirmed_export_range_verifies_declared_coverage(tmp_path: Path) -> None:
    name = "BBVA-Visa-Autorizaciones.csv"
    (tmp_path / name).write_text(
        "Fecha;Establecimiento;Moneda;Importe\n01/02/2025;Store;Pesos;3.00\n"
    )
    interval = {"kind": "transaction_dates", "start": "2025-02-01", "end": "2025-02-28"}
    manifest, _ = export_batch(
        tmp_path,
        [
            {
                "path": name,
                "system": "bbva_visa",
                "expected_coverage": [interval],
                "confirmed_export_range": {"start": "2025-02-01", "end": "2025-02-28"},
            }
        ],
    )
    assert manifest["complete"] is True
    assert manifest["expected_files"][0]["observed_coverage"] == [interval]


def test_unreadable_file_and_discarded_row_are_reported(tmp_path: Path) -> None:
    invalid = "BBVA-Visa-Autorizaciones-invalid.csv"
    (tmp_path / invalid).write_text("not a bank export\n")
    partial = "BBVA-Visa-Autorizaciones-partial.csv"
    (tmp_path / partial).write_text(
        "Fecha;Establecimiento;Moneda;Importe\n01/02/2025;Store;Pesos;3.00\nbad;Shop;Pesos;2.00\n"
    )
    manifest, records = export_batch(
        tmp_path,
        [
            {"path": invalid, "system": "bbva_visa", "expected_coverage": []},
            {"path": partial, "system": "bbva_visa", "expected_coverage": []},
        ],
    )
    assert len(records) == 1
    assert manifest["complete"] is False
    assert [item["status"] for item in manifest["expected_files"]] == [
        "unreadable",
        "partial",
    ]
    assert manifest["expected_files"][1]["rows_discarded"] == 1
    assert manifest["expected_files"][1]["warnings"][0]["locator"] == "row:3"


def test_mastercard_export_uses_close_cycle_and_preserves_old_installment(
    tmp_path: Path,
) -> None:
    class Detector:
        def detect_from_content(self, content: str) -> PaymentMethod:
            return PaymentMethod.BBVA_MASTERCARD

    class Factory:
        def create_parser(self, path: Path) -> PDFStatementParser:
            return parser

    name = "synthetic.pdf"
    (tmp_path / name).write_bytes(b"synthetic PDF placeholder")
    parser = PDFStatementParser(
        Detector(), TransactionBuilder(DateConverter(), AmountParser())
    )
    parser._extract_text = lambda path: (
        "CIERRE ACTUAL VENCIMIENTO ACTUAL SALDO ACTUAL $\n"
        "28-Ago-26 10-Sep-26 1.000,00 0,00 100,00\n"
        "CIERRE ANTERIOR VENCIMIENTO ANTERIOR PRÓXIMO CIERRE PRÓXIMO VENCIMIENTO\n"
        "31-Jul-26 10-Ago-26 30-Sep-26 10-Oct-26\n"
        "05-Apr-26 123456* STORE Cuota 03/06 25,00\n"
    )
    declaration = tmp_path / "declaration.json"
    declaration.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "files": [
                    {
                        "path": name,
                        "system": "bbva_mastercard",
                        "expected_coverage": [
                            {
                                "kind": "statement_cycle",
                                "start": "2026-08-01",
                                "end": "2026-08-28",
                            }
                        ],
                    }
                ],
            }
        )
    )
    manifest = export_reconciliation(declaration, tmp_path / "batch", Factory())
    record = json.loads((tmp_path / "batch" / "movements.jsonl").read_text())
    assert manifest["complete"] is True
    assert manifest["expected_files"][0]["rows_discarded"] == 0
    assert record["parsed"]["dates"] == [
        {"role": "purchase", "value": "2026-04-05"},
        {"role": "statement_close", "value": "2026-08-28"},
    ]
    assert record["raw"]["description"] == "STORE Cuota 03/06"
    assert record["references"]["Cuota"] == "03/06"


def test_pdf_description_separates_reference_and_amount() -> None:
    from datetime import date
    from decimal import Decimal

    from domain.models import Currency, SourceProvenance, Transaction
    from infrastructure.reconciliation_export import _observation

    transaction = Transaction(
        date(2025, 4, 1),
        "STORE",
        Decimal("25.00"),
        Currency.ARS,
        PaymentMethod.BBVA_VISA,
        provenance=SourceProvenance(
            "a" * 64,
            "line:3",
            "01.04.25",
            "25,00",
            "123456* STORE 25,00",
            references={"source_reference": "123456*"},
        ),
    )
    record = _observation(transaction, "bbva_visa", "file-1", None, is_pdf=True)
    assert record["raw"]["description"] == "STORE"
    assert record["raw"]["line_remainder"] == "123456* STORE 25,00"
    assert record["source"]["record_type"] == "statement_transaction"


def test_batch_id_depends_on_declared_inputs_not_directory(tmp_path: Path) -> None:
    ids = []
    for folder in (tmp_path / "one", tmp_path / "two"):
        folder.mkdir()
        (folder / "BBVA-Visa-Autorizaciones.csv").write_text("not a bank export\n")
        manifest, _ = export_batch(
            folder,
            [
                {
                    "path": "BBVA-Visa-Autorizaciones.csv",
                    "system": "bbva_visa",
                    "expected_coverage": [],
                }
            ],
        )
        ids.append(manifest["batch_id"])
    assert ids[0] == ids[1]
