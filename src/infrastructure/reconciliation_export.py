"""Write source observations and a verifiable v1 reconciliation manifest."""

import hashlib
import json
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from domain.factories import ParserFactory
from domain.models import PaymentMethod, Transaction

from .parsers.pdf_parser import PDFStatementParser


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _interval(value: dict[str, str]) -> dict[str, str]:
    start = date.fromisoformat(value["start"])
    end = date.fromisoformat(value["end"])
    if end < start:
        raise ValueError("Coverage end precedes start")
    return {"kind": value["kind"], "start": start.isoformat(), "end": end.isoformat()}


def _covered(expected: list[dict[str, str]], observed: list[dict[str, str]]) -> bool:
    return all(
        any(
            actual["kind"] == interval["kind"]
            and actual["start"] <= interval["start"]
            and actual["end"] >= interval["end"]
            for actual in observed
        )
        for interval in expected
    )


def _observation(
    transaction: Transaction,
    system: str,
    file_id: str,
    statement_close: str | None,
    *,
    is_pdf: bool,
) -> dict[str, Any]:
    provenance = transaction.provenance
    if provenance is None:
        raise ValueError("Parsed transaction lacks source provenance")
    identity = _digest(
        f"{system}\0{provenance.file_sha256}\0{provenance.locator}".encode()
    )
    date_role = "posted"
    if "TRANSACTION_DATE" in provenance.raw_dates:
        date_role = "transaction"
    elif transaction.payment_method == PaymentMethod.BBVA_MASTERCARD:
        date_role = "purchase"
    dates = [{"role": date_role, "value": transaction.date.isoformat()}]
    references = dict(provenance.references)
    if statement_close:
        dates.append({"role": "statement_close", "value": statement_close})
        references["statement_close"] = statement_close
    raw: dict[str, Any] = {
        "date": provenance.raw_date,
        "amount": provenance.raw_amount,
        "currency": provenance.raw_currency,
        "description": provenance.raw_description,
    }
    if is_pdf:
        remainder = provenance.raw_description
        reference = provenance.references.get("source_reference")
        if reference and remainder.startswith(f"{reference} "):
            remainder = remainder[len(reference) + 1 :]
        if provenance.raw_amount:
            remainder = re.sub(
                rf"\s+{re.escape(provenance.raw_amount)}\s*$", "", remainder
            )
        raw["description"] = remainder
        raw["line_remainder"] = provenance.raw_description
    if provenance.raw_dates:
        raw["dates"] = dict(provenance.raw_dates)
    return {
        "schema_version": "1.0",
        "observation_id": identity,
        "source": {
            "system": system,
            "record_type": "statement_transaction" if is_pdf else "export_transaction",
            "file_id": file_id,
            "locator": provenance.locator,
        },
        "native_ids": dict(provenance.native_ids),
        "source_identity": {"status": "unconfirmed", "key": None, "basis": []},
        "raw": raw,
        "parsed": {
            "amount": format(transaction.amount, "f"),
            "currency": transaction.currency.value,
            "dates": dates,
            "description": transaction.description,
        },
        "references": references,
        "diagnostics": [],
    }


def _file_entry(
    declared: dict[str, Any], base: Path, factory: ParserFactory
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    relative = Path(declared["path"])
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("Input paths must be relative to the declaration")
    system = declared["system"]
    if not isinstance(system, str) or not system:
        raise ValueError("Each file needs a source system")
    expected = [_interval(item) for item in declared["expected_coverage"]]
    file_path = base / relative
    entry: dict[str, Any] = {
        "file_id": _digest(f"unreadable\0{system}\0{relative}".encode()),
        "path": relative.as_posix(),
        "system": system,
        "expected_coverage": expected,
        "status": "missing",
        "observed_coverage": [],
        "rows_read": 0,
        "rows_emitted": 0,
        "rows_discarded": 0,
        "errors": [],
        "warnings": [],
        "sha256": None,
    }
    if not file_path.exists():
        entry["file_id"] = _digest(f"missing\0{system}\0{relative}".encode())
        entry["errors"].append(
            {"code": "missing_file", "message": "Declared file is missing"}
        )
        return entry, []
    try:
        file_hash = _digest(file_path.read_bytes())
        entry["sha256"] = file_hash
        entry["file_id"] = _digest(f"{system}\0{file_hash}".encode())
        parser = factory.create_parser(file_path)
        if isinstance(parser, PDFStatementParser):
            statement, content = parser.parse_with_content(file_path)
        else:
            statement = parser.parse(file_path)
            content = ""
        report = statement.extraction
        if report is None or report.file_sha256 != file_hash:
            raise ValueError("Parser did not return matching extraction evidence")
        entry["rows_read"] = report.rows_read
        entry["rows_emitted"] = report.rows_emitted
        entry["rows_discarded"] = report.rows_discarded
        for item in report.diagnostics:
            entry["warnings"].append(
                {
                    "code": "discarded_row",
                    "message": item.reason,
                    "locator": item.locator,
                }
            )
        close: str | None = None
        if (
            isinstance(parser, PDFStatementParser)
            and statement.payment_method == PaymentMethod.BBVA_MASTERCARD
        ):
            cycle = parser.statement_cycle(content)
            if cycle:
                start, end = cycle
                close = end.isoformat()
                entry["observed_coverage"].append(
                    {
                        "kind": "statement_cycle",
                        "start": start.isoformat(),
                        "end": close,
                    }
                )
            else:
                entry["warnings"].append(
                    {
                        "code": "cycle_unverified",
                        "message": "Mastercard close dates could not be verified",
                    }
                )
        if "confirmed_export_range" in declared:
            if file_path.suffix.lower() == ".pdf":
                raise ValueError("Confirmed export ranges apply only to tabular files")
            interval = _interval(
                {"kind": "transaction_dates", **declared["confirmed_export_range"]}
            )
            entry["observed_coverage"].append(interval)
        elif file_path.suffix.lower() != ".pdf":
            entry["warnings"].append(
                {
                    "code": "coverage_unverified",
                    "message": "Export date range was not confirmed",
                }
            )
        cycle_missing = (
            statement.payment_method == PaymentMethod.BBVA_MASTERCARD
            and file_path.suffix.lower() == ".pdf"
            and close is None
        )
        if (
            report.rows_discarded
            or cycle_missing
            or not _covered(expected, entry["observed_coverage"])
        ):
            entry["status"] = "partial"
            if not _covered(expected, entry["observed_coverage"]):
                entry["warnings"].append(
                    {
                        "code": "coverage_unmet",
                        "message": "Declared coverage was not verified",
                    }
                )
        else:
            entry["status"] = "complete"
        records = [
            _observation(
                txn,
                system,
                entry["file_id"],
                close,
                is_pdf=file_path.suffix.lower() == ".pdf",
            )
            for txn in statement.transactions
        ]
        if len(records) != report.rows_emitted:
            raise ValueError("Emitted row count differs from transactions")
        return entry, records
    except (OSError, ValueError, KeyError, TypeError) as exc:
        entry["status"] = "unreadable"
        entry["errors"].append({"code": "parse_failed", "message": str(exc)})
        entry["rows_emitted"] = 0
        return entry, []


def export_reconciliation(
    declaration_path: Path, output_dir: Path, factory: ParserFactory
) -> dict[str, Any]:
    """Export all declared source files, including missing and failed inputs."""
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    if declaration.get("schema_version") != "1.0":
        raise ValueError("Unsupported declaration schema_version")
    files = declaration.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Declaration needs a nonempty files array")
    paths = [item["path"] for item in files]
    if len(set(paths)) != len(paths):
        raise ValueError("Each declared input path must be unique")
    output_dir.mkdir(parents=True, exist_ok=True)
    movements_path = output_dir / "movements.jsonl"
    manifest_path = output_dir / "manifest.json"
    if movements_path.exists() or manifest_path.exists():
        raise FileExistsError("Export output already exists")
    entries: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for item in files:
        entry, file_records = _file_entry(item, declaration_path.parent, factory)
        entries.append(entry)
        records.extend(file_records)
    with movements_path.open("w", encoding="utf-8", newline="\n") as output:
        for record in records:
            output.write(
                json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
    payload = movements_path.read_bytes()
    scope_files = [
        {"declaration": declared, "sha256": entry["sha256"]}
        for declared, entry in zip(files, entries, strict=True)
    ]
    scope_files.sort(key=lambda item: item["declaration"]["path"])
    scope = json.dumps(scope_files, sort_keys=True, ensure_ascii=False).encode()
    manifest = {
        "schema_version": "1.0",
        "batch_id": _digest(scope),
        "generated_at": datetime.now(UTC).isoformat(),
        "movements": {
            "path": "movements.jsonl",
            "sha256": _digest(payload),
            "record_count": len(records),
        },
        "expected_files": entries,
        "complete": all(entry["status"] == "complete" for entry in entries),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
